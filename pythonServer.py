#!/usr/bin/env python
import SimpleHTTPServer
import SocketServer
import os
import rest_service
import re
import time
import database
from datetime import date, timedelta

class MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    serviceImpl = None
    database_service = None

    def do_GET(self):

        if self.serviceImpl is None:
            self.serviceImpl = rest_service.Runner(10)
            self.serviceImpl.initilize("job.properties",  "knoxPasswordFile.txt")
            self.database_service = database.DatabaseService()

        print self.path + os.getcwd()
        if self.path == '/':
            self.path = '/index.html'

        elif None != re.search("loadJobHistory", self.path):
            self.database_service.loadData()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write('{"response": { "message" : "Data loaded successfully"}}')
            return

        elif None != re.search("jobsInfo", self.path):
            d = date.today() - timedelta(days=7)
            allJobInfo = self.database_service.getAllJobs(d.strftime('%Y%m%d'))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(allJobInfo)
            return

        elif None != re.search("jobInfo/*", self.path):
            job_id = self.path.split("/")[-1]
            jobDetails = self.database_service.getOozieJobActions(job_id)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(jobDetails)
            return

        elif None != re.search("oozieJobInfo/*", self.path):

            wf_id = self.path.split("/")[-1]
            #wf_id = "0021801-141029175705544-oozie-oozi-W"
            jobInfo = self.serviceImpl.getOozieJobInfo(wf_id)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(jobInfo)
            return
        elif None != re.search("getFinishedJobs*", self.path):

            params = self.path.split("?")
            if None != params :
                paramValue = params[1].split("=")[1];
                currentTime = int(paramValue);
            else:
                currentTime = int(round(time.time() * 1000)) - (24 * 60 * 60 * 1000 * 2)
            print currentTime
            #wf_id = "0021801-141029175705544-oozie-oozi-W"
            jobInfo = self.serviceImpl.getJobHistory(currentTime)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(jobInfo)
            return
        return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

Handler = MyRequestHandler
server = SocketServer.TCPServer(('0.0.0.0', 9999), Handler)

server.serve_forever()