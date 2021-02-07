#!/usr/bin/python3
# -*- coding:utf-8 -*-

import threading

class ThreadManager():

    THREAD_PROFILE_PAGE_JOB = 1
    THREAD_RETRIEVE_RESOURCE_JOB = 2
    THREAD_COLLECT_RESOURCE_URL_JOB = 3
    THREAD_DOWNLOAD_JOB = 4

    THREAD_NUMBERS = {
        THREAD_PROFILE_PAGE_JOB: 200,
        THREAD_RETRIEVE_RESOURCE_JOB: 130,
        THREAD_COLLECT_RESOURCE_URL_JOB: 130,
        THREAD_DOWNLOAD_JOB: 100,
    }


    def __init__(self):
        self._thread_count = 0
        self._thread_list = []
        self._thread_pools = []

        self._url_workload = 0
        self._extra_url_worload = 0


    def _thread_func_args(self, i, thread_job, param_payload):
        if thread_job in (
            ThreadManager.THREAD_PROFILE_PAGE_JOB,
            ThreadManager.THREAD_RETRIEVE_RESOURCE_JOB,
            ThreadManager.THREAD_COLLECT_RESOURCE_URL_JOB):
            return (
                self._thread_pools,
                i,
                self._url_workload,
                self._extra_url_workload,
                param_payload
            )
        elif thread_job == ThreadManager.THREAD_DOWNLOAD_JOB:
            return (
                i, self._url_workload, self._extra_url_workload, param_payload
            )
        else:
            raise KeyError("Thread job doesn't exist")


    def thread_job_distribution(self, workload_url_count, thread_job):
        thread_number = ThreadManager.THREAD_NUMBERS[thread_job]
        if workload_url_count < thread_number:
            self._thread_count = workload_url_count
        else:
            self._thread_count = thread_number
        self._thread_pools = [[]] * self._thread_count
        self._url_workload = workload_url_count // self._thread_count
        self._extra_url_workload = workload_url_count % self._thread_count


    def thread_job_preparation(self, thread_func, thread_job, param_payload):
        for i in range(self._thread_count):
            thread = threading.Thread(
                target=thread_func,
                args=self._thread_func_args(
                    i, thread_job, param_payload
                )
            )
            self._thread_list.append(thread)


    def thread_job_handling(self, result_collector=None):
        for thread in self._thread_list:
            thread.setDaemon(True)
            thread.start()
        for thread in self._thread_list:
            thread.join()
        if result_collector is None:
            return
        for pool in self._thread_pools:
            result_collector += pool
