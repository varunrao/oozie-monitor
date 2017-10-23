from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import SimpleHTTPServer
from SocketServer import ThreadingMixIn
import threading
import rest_service
import re
import time
import os
from os import curdir, sep
import database
from mimetypes import MimeTypes
import urllib

class Handler(BaseHTTPRequestHandler):
    serviceImpl = None
    database_service = None
    mime = MimeTypes()

    def do_GET(self):

        #print self.path + os.getcwd()
        try:
            if self.serviceImpl is None:
                self.serviceImpl = rest_service.Runner(10)
                self.serviceImpl.initilize("job.properties",  "knoxPasswordFile.txt")
                self.database_service = database.DatabaseService()

                #print self.path + os.getcwd()

            if self.path == '/':
                self.path = '/index.html'

            if None != re.search("loadJobHistory", self.path):
                self.database_service.loadData()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write('{"response": { "message" : "Data loaded successfully"}}')
                return

            elif None != re.search("jobsInfo", self.path):
                allJobInfo = self.database_service.getAllJobs()
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

            else:
                sendReply = False
                if self.path.endswith(".html"):
                    mimetype='text/html'
                    sendReply = True
                elif self.path.endswith(".jpg"):
                    mimetype='image/jpg'
                    sendReply = True
                elif self.path.endswith(".gif"):
                    mimetype='image/gif'
                    sendReply = True
                elif self.path.endswith(".js"):
                    mimetype='application/javascript'
                    sendReply = True
                elif self.path.endswith(".css"):
                    mimetype='text/css'
                    sendReply = True
                elif None != re.search(".*woff", self.path):
                    self.path = "/bower_components/font-awesome/fonts/fontawesome-webfont.woff";
                    mimetype='application/font-woff'
                    #mimetype='font/opentype'
                    sendReply = True
                elif None != re.search(".*ttf", self.path):
                    mimetype='application/x-font-ttf'
                    self.path = "bower_components/font-awesome/fonts/fontawesome-webfont.ttf"
                    #mimetype='font/opentype'
                    sendReply = True
                elif None != re.search(".*svg", self.path):
                    mimetype='image/svg+xml'
                    #mimetype='font/opentype'
                    sendReply = True
                elif None != re.search(".*otf", self.path):
                    mimetype='application/x-font-opentype'
                    #mimetype='font/opentype'
                    sendReply = True
                elif None != re.search(".*eot", self.path):
                    mimetype='application/vnd.ms-fontobject'
                    #mimetype='font/opentype'
                    sendReply = True
                else:
                    url = urllib.pathname2url(self.path)
                    mime_type = self.mime.guess_type(url)
                    mimetype = mime_type[0]
                    print mimetype
                    sendReply = True
                    print self.path

                if sendReply == True:
                    #Open the static file requested and send it
                    f = open(curdir + sep + self.path, 'rb')
                    self.send_response(200)
                    self.send_header('Content-type',mimetype)
                    self.end_headers()
                    self.wfile.write(f.read())
                    f.close()
                return
        except IOError:
                self.send_error(404,'File Not Found: %s' % self.path)



class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('localhost', 9899), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()