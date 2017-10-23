'use strict';

/* Controllers
mdse_item_loc_import 'calendar_import','co_loc_import', 'code_catg_import'
'code_val_import','mdse_item_key_lkup_import'
'sls_type_med_type_prty_import'
*/
var referenceLoadJobs = ['ecom_item_import','mdse_item_key_lkup_import','co_loc_import','ecom_invc_import','sls_type_med_type_prty_import','sls_type_import','sls_actv_prc_var_reas_prty_import','code_val_import','code_catg_import','calendar_import','mdse_item_loc_import','pmtn_pgm_dim_import'];
var landingLoadJobs = ['eod_sls_e','sph870ia_vld_item_2_e','sph870ia_vld_item_1_e','sph865ia_tran_smry_2_e','sph865ia_tran_smry_1_e','sph861ia_item_xref_e','sph840id_tndr_det_1_e','cshr_spdc_e'];
var foundationLoadJobs = ['mdse_slstr_tax','eod_sls','sls_by_type_daily','rrt','rgtn','rgtn_tndr','tran_item_line_prc_adj','suplm_pharm_dspn_det','rrt_litm','mdse_slstr_item_line','mdse_slstr_fee','mdse_slstr_dsct'];
var countStatsReference = [];
var countStatsLanding = [];
var countStatsFoundation = [];


var jobsToTrack = ['sls_by_type_daily','rrt','rgtn','rgtn_tndr','tran_item_line_prc_adj','suplm_pharm_dspn_det','rrt_litm','mdse_slstr_item_line','mdse_slstr_fee','mdse_slstr_dsct'];
var jobsToTrackHighCharts = ['sls_by_type_daily','rrt','rgtn','rgtn_tndr','tran_item_line_prc_adj','suplm_pharm_dspn_det','rrt_litm','mdse_slstr_item_line','mdse_slstr_fee','mdse_slstr_dsct'];
var seriesData = {};
var dataTable;
var dataTableCounts;

var categoryHC = [];
var seriesDataHC = []
var seriesDataHCScatter = [];

function secondsToString(seconds)
{
var numhours = Math.floor(((seconds % 31536000) % 86400) / 3600);
var numminutes = Math.floor((((seconds % 31536000) % 86400) % 3600) / 60);
var numseconds = (((seconds % 31536000) % 86400) % 3600) % 60;
if(numhours != 0)
    return numhours + " hours " + numminutes + " minutes " + numseconds + " seconds";
else
    return numminutes + " minutes " + numseconds + " seconds";
}

var dashBoardController = angular.module('dashBoardController', []);

dashBoardController.controller('JobHistoryControllerV2', ['$scope', 'JobHistory', 'OozieJobInfo',
  function($scope, JobHistory, OozieJobInfo) {
    $scope.showData = function() {
        $scope.loading = true;
        if(typeof dataTable == "undefined") {
            dataTable = $('#jobHistory').dataTable(
                {
                    responsive: true
                }
            );
        }

        if(typeof dataTableCounts == "undefined") {
            dataTableCounts = $('#jobCounts').dataTable(
                {
                    responsive: true
                }
            );
        }
        //Initialize all the job data
        initializeJobData();
        dataTable.DataTable().clear();

        var promiseAllJob = JobHistory.getAllJobs();
        var elaspedTime,timeInMinutes,startDate,formatedStartDate,seriesTime,formatedStartDateWithMin;
        promiseAllJob.then(function(jobInfo) {
             dataTable.DataTable().clear().draw();
             for (var jobIndex = 0; jobIndex < jobInfo.data.length; jobIndex++) {
                var job = jobInfo.data[jobIndex];
                startDate = new Date(job.start_time);
                formatedStartDate = (startDate.getMonth() + 1) + "/" + startDate.getDate() + "/" + startDate.getFullYear();
                if($.inArray(formatedStartDate, categoryHC) == -1) {
                   categoryHC.push(formatedStartDate);
                }
             }

             for (var jobIndex = 0; jobIndex < jobInfo.data.length; jobIndex++) {
                 var job = jobInfo.data[jobIndex];
                 elaspedTime = secondsToString(Math.abs(new Date(job.end_time) - new Date(job.start_time))/1000);
                 timeInMinutes = (Math.abs(new Date(job.end_time) - new Date(job.start_time))/(1000 * 60));
                 timeInMinutes = parseFloat(Math.round(timeInMinutes * 100) / 100);
                 startDate = new Date(job.start_time);
                 formatedStartDate = (startDate.getMonth() + 1) + "/" + startDate.getDate() + "/" + startDate.getFullYear();
                 formatedStartDateWithMin = (startDate.getMonth() + 1) + "/" + startDate.getDate() + "/" + startDate.getFullYear() + " " + startDate.getHours() + ":" + startDate.getMinutes();
                 //Load into arry for job counts
                 //Loads the run stats based on the job info
                 loadRunStats(job);

                 if ($.inArray(job.name, jobsToTrackHighCharts) != -1 && job.status == "SUCCEEDED") {
                     if(typeof seriesDataHC[job.name] == 'undefined') {
                        var jobData = {"name" : "", "data" : []};
                        var jobDataScatter = {"name" : "", "data" : []};

                        jobData['name'] = job.name;
                        jobDataScatter['name'] = job.name;
                        jobData['data'] = [];
                        jobDataScatter['data'] = [];

                        for(var i = 0 ; i < categoryHC.length; i++) {
                            jobData['data'][i] = [];
                            //jobDataScatter['data'][i] = 0;
                        }
                        seriesDataHC[job.name] = jobData;
                        seriesDataHCScatter[job.name] = jobDataScatter;
                     }
                    seriesTime = timeInMinutes;
                    //if(seriesDataHC[job.name]['data'][$.inArray(formatedStartDate, categoryHC)] != null)
                    //    seriesTime = (timeInMinutes + seriesDataHC[job.name]['data'][$.inArray(formatedStartDate, categoryHC)]) / 2;
                    //else
                    //    seriesTime = timeInMinutes;
                    seriesDataHC[job.name]['data'][$.inArray(formatedStartDate, categoryHC)].push(parseFloat(Math.round(seriesTime * 100) / 100));

                    if(job.status == "FAILED" || job.status == "KILLED")
                        seriesDataHCScatter[job.name]['data'].push({x:startDate.getTime(), y:parseFloat(Math.round(seriesTime * 100) / 100), fillColor:'#FF0000'});
                    else
                        seriesDataHCScatter[job.name]['data'].push({x:startDate.getTime(), y:parseFloat(Math.round(seriesTime * 100) / 100)});
                 }


                 if( typeof seriesData[formatedStartDate] == 'undefined') {
                    seriesData[formatedStartDate] = new Array(jobsToTrack.length);
                    for(var i = 0 ; i < seriesData[formatedStartDate].length; i++)
                        seriesData[formatedStartDate][i] = 0;

                    seriesData[formatedStartDate][0] = formatedStartDate;
                 }
                 if($.inArray(job.name, jobsToTrack) != -1)
                    seriesData[formatedStartDate][$.inArray(job.name, jobsToTrack)] = timeInMinutes;
                 //setTimeout(function() {
                 dataTable.DataTable().row.add([
                                job.name,
                                (job.status == "SUCCEEDED" ? job.status : "ERROR-"+job.status),
                                formatedStartDateWithMin,
                                timeInMinutes,
                                elaspedTime,
                                "<a href='javascript:;'>"+job.job_id+"</a>"
                            ]).draw();
                  //}, 1);

            }
            //dataTable.rowGrouping({	bExpandableGrouping: true,
            //                    bExpandSingleGroup: true,
            //                    iExpandGroupOffset: -1 });
            $scope.loading = false;
            //createChart();
            createHighCarts();
            //createHighCartsScatter();
            loadCountsTable();

            },function(errorPayload){
            }
            );
    };
    $scope.reloadJobHistory = function() {
        $scope.loading = true;
        var promiseLoad = JobHistory.loadJobHistory();
        promiseLoad.then(function(payload) {
            $scope.loading = false;
            $scope.showData();

        });
    };
    $scope.showData();

    }
    ]);

function initializeJobData() {
    countStatsReference = [];
    countStatsLanding = [];
    countStatsFoundation = [];
    seriesData = {};
    categoryHC = [];
    seriesDataHC = []
    seriesDataHCScatter = [];


    for (var jobIndex = 0; jobIndex < referenceLoadJobs.length; jobIndex++) {
        if(typeof countStatsReference[referenceLoadJobs[jobIndex]] == 'undefined') {
            var jobData = {"name" : referenceLoadJobs[jobIndex], "total" : 0, "success" : 0, "fail" : 0, "jobs" :[]};
            countStatsReference[referenceLoadJobs[jobIndex]]  = jobData;
        }
    }

    for (var jobIndex = 0; jobIndex < landingLoadJobs.length; jobIndex++) {
        if(typeof countStatsLanding[landingLoadJobs[jobIndex]] == 'undefined') {
                var jobData = {"name" : landingLoadJobs[jobIndex], "total" : 0, "success" : 0, "fail" : 0, "jobs": []};
                countStatsLanding[landingLoadJobs[jobIndex]]  = jobData;
            }
    }

    for (var jobIndex = 0; jobIndex < foundationLoadJobs.length; jobIndex++) {
        if(typeof countStatsFoundation[foundationLoadJobs[jobIndex]] == 'undefined') {
                var jobData = {"name" : foundationLoadJobs[jobIndex], "total" : 0, "success" : 0, "fail" : 0, "jobs":[]};
                countStatsFoundation[foundationLoadJobs[jobIndex]]  = jobData;
            }
    }

}

function loadRunStats(job) {
      var total, success, fail, countStats;
      var timeInMinutes = (Math.abs(new Date(job.end_time) - new Date(job.start_time))/(1000 * 60));
      timeInMinutes = parseFloat(Math.round(timeInMinutes * 100) / 100);

     if($.inArray(job.name, referenceLoadJobs) != -1 || $.inArray(job.name, landingLoadJobs) != -1 || $.inArray(job.name, foundationLoadJobs) != -1)
     {
          if($.inArray(job.name, referenceLoadJobs) != -1)
            countStats = countStatsReference;
          if($.inArray(job.name, landingLoadJobs) != -1)
            countStats = countStatsLanding;
          if($.inArray(job.name, foundationLoadJobs) != -1)
            countStats = countStatsFoundation;


          total = countStats[job.name].total;
          total = total + 1;
          countStats[job.name].total = total;
          if(job.status == "SUCCEEDED") {
            success = countStats[job.name].success;
            success = success + 1;
            countStats[job.name].success = success;
            countStats[job.name].jobs.push(timeInMinutes);
          }
          else {
            fail = countStats[job.name].fail;
            fail = fail+1;
            countStats[job.name].fail = fail;
          }
     }


}

function loadCountsTable() {
    dataTableCounts.DataTable().clear();

    var allJobs = [];
    allJobs.push(countStatsReference);
    allJobs.push(countStatsLanding);
    allJobs.push(countStatsFoundation);
    var countStats;

    for(var outletIndex = 0; outletIndex < allJobs.length; outletIndex++) {
    countStats = allJobs[outletIndex];

    for (var key in countStats) {
        var jobData = countStats[key];
        if(jobData.name) {
            dataTableCounts.DataTable().row.add([
                                    jobData.name,
                                    ($.inArray(jobData.name, referenceLoadJobs) != -1 ? "reference" : ($.inArray(jobData.name, landingLoadJobs)) != -1? "landing" : "foundation"),
                                    jobData.total,
                                    "<a href='javascript:filterMainData(\""+jobData.name+"\", \"SUCCEEDED\")'>" + jobData.success+"</a>",
                                    "<a href='javascript:filterMainData(\""+jobData.name+"\", \"ERROR\")'>" + jobData.fail + "</a>",
                                    jobData.jobs.average()
                                ]).draw();
            }
    }
}

}

function filterMainData(jobName, status) {
    dataTable.DataTable().search(jobName + " " + status).draw();
}

function filterCountsData(jobName) {
    dataTableCounts.DataTable().search(jobName).draw();
}

function getChartData() {
    var data = [];
    var rowIndex = 0;

    data[rowIndex++] = jobsToTrack;

    for (var key in seriesData) {
        data[rowIndex++] = seriesData[key];
    }

    dataTable = new google.visualization.DataTable();
    var numRows = data.length;
    var numColumns = data[0].length;

    dataTable.addColumn('string', data[0][0]);

    for(var i = 1; i < numColumns; i++)
        dataTable.addColumn('number', data[0][i]);
    //dataTable.addColumn({role: 'annotation'});

    for(var i = 1; i < numRows; i++)
        dataTable.addRow(data[i]);

    return dataTable;
}

function createChart() {


        var options = {
          title: 'Oozie job timmings',
          legend: { position: 'right' },
          height : 800
//          ,
//          vAxis: {
//            ticks: [0,5,10,15]
//          }
        };

        var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

        chart.draw(getChartData(), options);
}

function getHighCartsCategories(){
    //var categories = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return categoryHC;
}

function getHighChartsSeriesData()
{
    var localSeriesData = [];

    for (var key in seriesDataHC) {
        var dataArray = seriesDataHC[key]['data'];
        var newArray = [];
        if(dataArray) {
            for (var indexData = 0; indexData < dataArray.length; indexData++) {
                if(dataArray[indexData].length == 0)
                    newArray.push(0);
                else
                   newArray.push(dataArray[indexData].average())
            }
            seriesDataHC[key]['data']=newArray;
            localSeriesData.push(seriesDataHC[key])
        }
     }
    return localSeriesData;
}

function getHighChartsScatterSeriesData()
{
    var localSeriesData = [];

    for (var key in seriesDataHCScatter)
        localSeriesData.push(seriesDataHCScatter[key])
    return localSeriesData;
}

function createHighCarts()
{

    $('#highChart').highcharts({
        chart: {
            zoomType: 'xy',
//            events: {
//                    load: function() {
//                        StaggerDataLabels(this.series);
//                    },
//                    redraw: function() {
//                        var series = this.series;
//                        setTimeout(function() {
//                            StaggerDataLabels(series);
//                        }, 1000);
//                    }
//                },
                type: 'column'
        },
        title: {
            text: 'Oozie Job timmings'
        },
        subtitle: {
            text: 'Source: Ooozie job info'
        },
        xAxis: {
            categories: getHighCartsCategories(),
            labels: {
                enabled:true,
                y:20,
                overflow: 'justify',
                rotation:-45,
                align: 'right'
            }
        },
        yAxis: {
            title: {
                text: 'Time in minutes'
            }
        },
        legend: {
                layout: 'vertical',
                backgroundColor: '#FFFFFF',
                align: 'left',
                verticalAlign: 'top',
                x: 70,
                y: 0,
                floating: true,
                shadow: true
            },
        plotOptions: {
            column: {
               dataLabels: {
                        overflow: 'none',
                        crop: false,
                        enabled: true,
                        allowOverlap: false,
                        formatter: function() {
                            if(this.y != 0)
                                return (this.y);
                        }
                },
                enableMouseTracking: true,
                point: {
                    events: {
                        click: function() {
                            filterMainData(this.series.name, this.category);
                            filterCountsData(this.series.name);
                        }
                    }
                }
            }
        },
        tooltip: {
            //crosshairs: [true, true],
            followPointer:true,
            formatter: function() {
               return  '<b>' + this.series.name + '</b> - <b>' + this.x +'</b>-average: ' + this.y;
            }
        },
        series: getHighChartsSeriesData()
    });
}

function StaggerDataLabels(series) {
    var sc = series.length;
    if (sc < 2) return;

    for (var s = 1; s < sc; s++) {
        var s1 = series[s - 1].points,
            s2 = series[s].points,
            l = s1.length,
            diff, h;

        for (var i = 0; i < l; i++) {
            if (s2[i] && s1[i] && s1[i].dataLabel && s2[i].dataLabel) {
                diff = s1[i].dataLabel.y - s2[i].dataLabel.y;
                h = s1[i].dataLabel.height + 2;

                if (isLabelOnLabel(s1[i].dataLabel, s2[i].dataLabel)) {
                    if (diff < 0) s1[i].dataLabel.translate(s1[i].dataLabel.translateX, s1[i].dataLabel.translateY - (h + diff));
                    else s2[i].dataLabel.translate(s2[i].dataLabel.translateX, s2[i].dataLabel.translateY - (h - diff));
                }
            }
        }
    }
}

//compares two datalabels and returns true if they overlap


function isLabelOnLabel(a, b) {
    var al = a.x - (a.width / 2);
    var ar = a.x + (a.width / 2);
    var bl = b.x - (b.width / 2);
    var br = b.x + (b.width / 2);

    var at = a.y;
    var ab = a.y + a.height;
    var bt = b.y;
    var bb = b.y + b.height;

    if (bl > ar || br < al) {
        return false;
    } //overlap not possible
    if (bt > ab || bb < at) {
        return false;
    } //overlap not possible
    if (bl > al && bl < ar) {
        return true;
    }
    if (br > al && br < ar) {
        return true;
    }

    if (bt > at && bt < ab) {
        return true;
    }
    if (bb > at && bb < ab) {
        return true;
    }

    return false;
}


function createHighCartsScatter() {
    $('#highChart').highcharts({
        chart: {
            type: 'scatter'
            //zoomType: 'xy'
        },
        title: {
            text: 'Oozie Job timmings'
        },
        subtitle: {
            text: 'Source: Ooozie job info'
        },
        xAxis: {
            type: 'datetime',
            labels: {
                enabled:true,
                y:20,
                overflow: 'justify',
                rotation:-45,
                align: 'right',
                formatter: function() {
                    return Highcharts.dateFormat('%m/%d/%Y', this.value);
                }
            },
            title: {
                enabled: true,
                text: 'dates',
            },
            startOnTick: true,
            endOnTick: true,
            showLastLabel: true
        },
        yAxis: {
            title: {
                text: 'Time in minutes'
            }
        },
        tooltip: {
            formatter: function() {
               return  Highcharts.dateFormat('%m/%d/%Y', this.x) + '<br>' + this.y;
            }
        },
        plotOptions: {
            scatter: {
                marker: {
                    radius: 4,
                    states: {
                        hover: {
                            enabled: true,
                            lineColor: 'rgb(100,100,100)'
                        }
                    }
                },
                states: {
                    hover: {
                        marker: {
                            enabled: false
                        }
                    }
                }
            }
        },
        series: getHighChartsScatterSeriesData()
    });
}


Array.prototype.max = function() {
  return Math.max.apply(null, this);
};

Array.prototype.min = function() {
  return Math.min.apply(null, this);
};

Array.prototype.average=function(){
    var sum=0;
    var j=0;
    for(var i=0;i<this.length;i++){
        if(isFinite(this[i])){
          sum=sum+parseFloat(this[i]);
           j++;
        }
    }
    if(j===0){
        return 0;
    }else{
        return parseFloat(Math.round((sum/j) * 100) / 100);
    }

}