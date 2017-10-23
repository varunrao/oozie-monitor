'use strict';

/* App Module */

var phonecatApp = angular.module('phonecatApp', [
  'ngRoute',
  'ng',
   'ngResource',
  'dashBoardController',
  'restServices',
  'datatables'
]);

phonecatApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/jobHistory', {
        templateUrl: 'view/jobHistory.html'
        //controller: 'JobHistoryControllerV2'
      }).
      when('/errorJobs', {
        templateUrl: 'view/errorJobs.html',
        controller: 'ErrorController'
      }).
      otherwise({
        redirectTo: '/jobHistory'
      });
  }]);

