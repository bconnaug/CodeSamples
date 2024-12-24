package main

import (
	"container/list"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"math"
	"os"
	"strconv"

	"github.com/cmu440/bitcoin"
	"github.com/cmu440/lsp"
)

type server struct {
	lspServer      lsp.Server
	maxChunkSize   uint64
	clientMessages map[int]*bitcoin.Message
	miners         map[int]*Job
	clients        *list.List
	results        map[int]*bitcoin.Message
	idleMinerJobs  *list.List
}

type Job struct {
	clientConnID int
	upper        uint64
	message      *bitcoin.Message
}

/*
Initalizes the lsp server and, if possible, all relevant fields
*/
func startServer(port int) (*server, error) {
	lspServer, err := lsp.NewServer(port, lsp.NewParams())
	if err != nil {
		return nil, errors.New("could not start server on port")
	}
	maxChunkSize := uint64(10000)
	srv := &server{
		lspServer:      lspServer,
		maxChunkSize:   maxChunkSize,
		clientMessages: make(map[int]*bitcoin.Message),
		miners:         make(map[int]*Job),
		clients:        list.New().Init(),
		results:        make(map[int]*bitcoin.Message),
		idleMinerJobs:  list.New().Init(),
	}
	return srv, nil
}

var LOGF *log.Logger

/*
Distributes available server jobs to available miners.
Does this fairly with a round robin-like algorithm, where we rotate
clients in the srv.clients list as long as they have not receieved a result
message for all segments of their original message
*/
func distributeJob(srv *server, connID int) {
	nextMiner := srv.idleMinerJobs.Back()
	if nextMiner != nil {
		miner := nextMiner.Value.(*Job)
		srv.miners[connID] = miner
		marshal, err := json.Marshal(miner.message)
		if err != nil {
			return
		}
		srv.lspServer.Write(connID, marshal)
		srv.idleMinerJobs.Remove(nextMiner)
	} else {
		sentLastPiece := false
		lastClient := srv.clients.Back()
		if lastClient != nil {
			clientConnID := lastClient.Value.(int)

			msg1 := srv.clientMessages[clientConnID]

			data := msg1.Data
			lower := msg1.Lower
			upper := msg1.Upper
			newUpper := lower + srv.maxChunkSize

			var req *bitcoin.Message
			if newUpper <= upper {
				req = bitcoin.NewRequest(data, lower, newUpper)
				msg1.Lower = newUpper
			} else {
				sentLastPiece = true
				newUpper = upper
				req = bitcoin.NewRequest(data, lower, newUpper)
				msg1.Lower = upper
			}
			msg, err := json.Marshal(req)
			if err != nil {
				return
			}

			newJob := &Job{clientConnID: clientConnID, upper: newUpper, message: req}
			srv.miners[connID] = newJob

			srv.lspServer.Write(connID, msg)
			if !sentLastPiece {
				srv.clients.MoveToFront(lastClient)
			} else {
				srv.clients.Remove(lastClient)
			}
		}
	}
}

/*
Deletes a client from the client list.
*/
func deleteClient(srv *server, clientConnID int) {
	client := srv.clients.Front()
	if client == nil {
		return
	}
	for client != nil {
		if client.Value == clientConnID {
			srv.clients.Remove(client)
			break
		} else {
			client = client.Next()
		}
	}
}

/*
Deletes all pieces of a client's job from the idle job list.
*/
func deleteClientJob(srv *server, clientConnID int) {
	job := srv.idleMinerJobs.Front()
	if job == nil {
		return
	}
	for job != nil {
		jobVal := job.Value.(*Job)
		if jobVal.clientConnID == clientConnID {
			placeholder := job
			job = job.Next()
			srv.idleMinerJobs.Remove(placeholder)
		} else {
			job = job.Next()
		}
	}
}

/*
In the case that a client or miner connection is dropped, this function handles
the corresponding job.
If the miner connection is dropped, delete it from our records and pass its
task to the next available miner.
If the client connection is dropped, delete it and all segments of its request
from our records.
*/
func serverIlliterate(srv *server, connID int, msg *bitcoin.Message) {
	switch msg.Type {
	case bitcoin.Join:
		// miner sends join request to server
		idleJob := srv.miners[connID]
		if idleJob != nil {
			// give job to another miner later if it exists
			srv.idleMinerJobs.PushFront(idleJob)
		}
		delete(srv.miners, connID)
		delete(srv.clientMessages, connID)

		for clientConnID, job := range srv.clientMessages {
			if job != nil {
				distributeJob(srv, clientConnID)
				break
			}
		}
	case bitcoin.Request:
		// client disconnected from server
		delete(srv.miners, connID)
		delete(srv.clientMessages, connID)
		deleteClient(srv, connID)
		deleteClientJob(srv, connID)
	case bitcoin.Result:
		// handle just like Join messages, since both are sent by miners
		return
	}
}

func main() {
	// You may need a logger for debug purpose
	const (
		name = "serverLog.txt"
		flag = os.O_RDWR | os.O_CREATE
		perm = os.FileMode(0666)
	)

	file, err := os.OpenFile(name, flag, perm)
	if err != nil {
		return
	}
	defer file.Close()

	LOGF = log.New(file, "", log.Lshortfile|log.Lmicroseconds)
	// Usage: LOGF.Println() or LOGF.Printf()

	const numArgs = 2
	if len(os.Args) != numArgs {
		fmt.Printf("Usage: ./%s <port>", os.Args[0])
		return
	}

	port, err := strconv.Atoi(os.Args[1])
	if err != nil {
		fmt.Println("Port must be a number:", err)
		return
	}

	srv, err := startServer(port)
	if err != nil {
		fmt.Println(err.Error())
		return
	}

	defer srv.lspServer.Close()

	for {
		var msg *bitcoin.Message
		connID, payload, err := srv.lspServer.Read()
		json.Unmarshal(payload, &msg)
		if err != nil {
			// connection dropped from miner or client
			clientMsg, exists := srv.clientMessages[connID]
			if exists {
				serverIlliterate(srv, connID, clientMsg)
			}
			continue
		} else {
			switch msg.Type {
			case bitcoin.Join:
				minerConnID := connID
				srv.clientMessages[minerConnID] = msg
				srv.miners[minerConnID] = nil
				distributeJob(srv, connID)
			case bitcoin.Request:
				clientConnID := connID

				srv.clients.PushFront(clientConnID)
				srv.clientMessages[clientConnID] = msg
				// assume the result hash and nonce at the largest possible value and decrease from there
				srv.results[clientConnID] = bitcoin.NewResult(uint64(math.MaxUint64), (uint64(math.MaxUint64)))
				// distribute split-up job to avaiable miners
				for minerConnID, _ := range srv.miners {
					if srv.miners[minerConnID] == nil {
						distributeJob(srv, minerConnID)
					}
				}
			case bitcoin.Result:
				minerConnID := connID
				job := srv.miners[minerConnID]
				srv.miners[minerConnID] = nil
				distributeJob(srv, minerConnID)
				// delete client from our records if possible
				request, exists := srv.clientMessages[job.clientConnID]
				if !exists {
					continue
				}
				// calculate min hash value from result segments
				clientConnID := job.clientConnID
				if msg.Hash < srv.results[clientConnID].Hash {
					srv.results[clientConnID] = msg
				}
				// if we got all segments for a given request, send the min hash
				// and corresponding nonce values to the client
				if job.upper == request.Upper {
					delete(srv.clientMessages, clientConnID)
					marshal, err := json.Marshal(srv.results[clientConnID])
					if err != nil {
						continue
					}
					srv.lspServer.Write(clientConnID, marshal)
					delete(srv.results, clientConnID)
				}
			}
		}
	}
}
