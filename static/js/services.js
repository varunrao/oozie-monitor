'use strict';

/* Services */

var restServices = angular.module('restServices', ['ngResource']);

restServices.factory('JobHistory', ['$http',
  function($http,$resource){

	    this.getJobHistory = function (startTime) {
		    return $http.get(
		    		'/getFinishedJobs?startTime='+startTime
		    	);
		};

		this.loadJobHistory = function () {
		    return $http.get(
		    		'/loadJobHistory'
		    	);
		};
        this.getAllJobs = function () {
		    return $http.get(
		    		'/jobsInfo'
		    	);
		};

        this.getJobDetails = function (jobId) {
		    return $http.get(
		    		'/jobInfo/' + jobId
		    	);
		};

		return this;
  }]);

restServices.factory('OozieJobInfo', ['$resource',
  function($resource){

	    this.getOozieJobInfo = function () {
		    return $resource(
		    		'/oozieJobInfo/:jobId', {jobId:'@jobId'}
		    	);
		};
		return this;
  }]);


