import collections
import csv
import datetime
import logging
import os
import threading

import numpy as np

log = logging.getLogger()
log.setLevel(logging.DEBUG)



class DataStore:
    def __init__(self, sensor_inst, csv_out_file, max_num_items):
        self.sensor_ = sensor_inst
        self.csv_out_  = csv_out_file
        self.mutex_ = threading.Lock()
        self.max_items_ = max_num_items
        self.worker_en_ = True
        self.csv_writer_ = None

        self.init()
        self.worker_thread_ = threading.Thread(target=self.worker, name="data_worker")
        self.worker_thread_.start()


    def init(self):
        self.errors_allowed_ = 1000
        # keep separate lists, for faster separate handling (np.asarray()!)
        self.qtime_ = []
        self.qtorque_ = []
        self.qspeed_ = []
        self.qpower_ = []
        self.queues_ = (self.qtime_, self.qtorque_, self.qspeed_, self.qpower_)
        self.csv_file_ = open(self.csv_out_, "w", newline="")
        self.csv_writer_ = csv.writer(self.csv_file_)
        log.info(f"logging to >{self.csv_out_}<")
        self.csv_writer_.writerow(("experiment time [s]", "torque [Nm]", "rotation speed [1/s]", "power [W]"))
        self.t_start_ = datetime.datetime.now()

        latest_file = os.path.dirname(self.csv_out_) + "/latest"

        if os.path.exists(latest_file):
            os.unlink(latest_file)

        os.symlink(self.csv_out_, latest_file)


    def worker(self):
        while self.worker_en_:
            try:
                t_now = datetime.datetime.now()
                dt = (t_now - self.t_start_).total_seconds()
                t, s, p = self.sensor_.get_torque_speed_power()

                with self.mutex_:
                    for q, val in zip(self.queues_, (dt, t, s, p)):
                        q.append(val)

                    if len(self.qtime_) > self.max_items_:
                        self.data_write_oldest()

            except Exception as e:
                self.errors_allowed_ -= 1

                if self.errors_allowed_ > 0:
                    log.error(f"something went wrong: {e}")
                else:
                    raise e


    def data_get(self):
        """
        @returns list of the data in np arrays
        """
        return [np.asarray(x) for x in self.queues_]


    def data_write_oldest(self):
        """
        write the oldest entry from each list and discard them
        """
        row = [x.pop(0) for x in self.queues_]

        if self.csv_writer_ is not None:
            self.csv_writer_.writerow(row)


    def shutdown(self):
        """
        terminate and join worker threads, then write all data from the queues to file
        """
        self.worker_en_ = False
        log.info("waiting for DataSource worker..")
        self.worker_thread_.join()
        log.info("DataSource worker terminated.")
        log.info("writing data from buffer...")

        while len(self.qtime_) > 0:
            self.data_write_oldest()

        if self.csv_writer_:
            self.csv_file_.close()
            self.csv_writer_ = None

        log.info("wrote data store to file.")
