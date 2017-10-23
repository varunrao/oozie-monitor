#!/usr/bin/env python
from flask import Flask, render_template, send_from_directory
import os
import rest_service
import re
import time
import database
from datetime import date, timedelta

app = Flask(__name__)

serviceImpl = None
database_service = None

@app.route("/")
def index():
    global serviceImpl
    global database_service
    if serviceImpl is None or database_service is None:
        serviceImpl = rest_service.Runner(10)
        serviceImpl.initilize("job.properties",  "knoxPasswordFile.txt")
        database_service = database.DatabaseService()
        print "Service impl initialized"
    return send_from_directory('.','index.html')

@app.route("/static/<path:path>")
def appJS(path):
    return send_from_directory('static',path)

@app.route("/ZeroClipboard/<path:path>")
def zeroClipBoard(path):
    return send_from_directory('ZeroClipboard',path)

@app.route("/view/<path:path>")
def viewFiles(path):
    return send_from_directory('view',path)

@app.route("/data/<path:path>")
def viewDataFiles(path):
    return send_from_directory('data',path)

@app.route("/media/<path:path>")
def mediaFiles(path):
    return send_from_directory('media',path)

@app.route("/proposal.html")
def showProposal():
    return send_from_directory('.','proposal.html')

@app.route("/loadJobHistory")
def loadJobHistory():
    database_service.loadData()
    return '{"response": { "message" : "Data loaded successfully"}}'

@app.route("/jobsInfo")
def getJobsInfo():
    d = date.today() - timedelta(days=7)
    allJobInfo = database_service.getAllJobs(d.strftime('%Y%m%d'))
    #allJobInfo = database_service.getAllJobs()
    return allJobInfo

@app.route("/jobsInfo/<jobId>")
def getJobInfo(jobId):
    jobDetails = database_service.getOozieJobActions(jobId)
    return jobDetails

@app.route("/oozieJobInfo/<oozieJobId>")
def getOozieJobInfo(oozieJobId):
    jobInfo = serviceImpl.getOozieJobInfo(oozieJobId)
    return jobInfo

@app.route("/getFinishedJobs?<query>")
def getFinishJobs(query):
    params = query
    if None != params :
        paramValue = params[1].split("=")[1];
        currentTime = int(paramValue);
    else:
        currentTime = int(round(time.time() * 1000)) - (24 * 60 * 60 * 1000 * 2)
    print currentTime
    jobInfo = serviceImpl.getJobHistory(currentTime)
    return jobInfo

if __name__ == "__main__":
  app.debug = True
  app.run(host="brdlx0004.hq.target.com", port=10005)