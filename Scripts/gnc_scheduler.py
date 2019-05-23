############################################################
# LICENSE
# Copyright (C) 2018 - INPE - NATIONAL INSTITUTE FOR SPACE RESEARCH
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
############################################################

import sched, time # Scheduler library
import os          # Miscellaneous operating system interfaces         

# Python environment (Windows)
#python_env = 'C://Users//dsouza//Anaconda3//envs//geonetcast3//'
python_env = 'C://Users//dsouza//Anaconda3//envs//satpy2//'

# GEONETCast-Americas ingestion directory (Windows)
gnc_dir = 'D://VLAB//GNC-Samples-2019-01-12//'

# Python environment (Linux)
#python_env = '//root//miniconda3//envs//geonetcast//bin//'

# GEONETCast-Americas ingestion directory (Linux)
#gnc_dir = '//dados//fazzt//'

# Interval in seconds
seconds = 60

# Call the function for the first time without the interval
print("\n")
print("------------- Calling Monitor Script --------------")
script = python_env + 'python gnc_monitor.py' + ' ' + python_env + ' ' + gnc_dir		
os.system(script)
print("------------- Monitor Script Executed -------------")
print("Waiting for next call. The interval is", seconds, "seconds.")
	
# Scheduler function
s = sched.scheduler(time.time, time.sleep)

def call_monitor(sc): 
    print("\n")
    print("------------- Calling Monitor Script --------------")
    script = python_env + 'python gnc_monitor.py' + ' ' + python_env + ' ' + gnc_dir		
    os.system(script)
    print("------------- Monitor Script Executed -------------")
    print("Waiting for next call. The interval is", seconds, "seconds.")	
    s.enter(seconds, 1, call_monitor, (sc,))
    # Keep calling the monitor
	
# Call the monitor
s.enter(seconds, 1, call_monitor, (s,))
s.run()


