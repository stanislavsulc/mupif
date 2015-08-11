#!/bin/bash

# accumulates failures, which are stored in $ret for each example
retval=0

pushd Example01; 
	echo $PWD
	python Example01.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example02
	echo $PWD
	python nameserver.py &
	PID1=$!
	echo PID $PID1
	sleep 1
	python server.py &
	PID2=$!
	echo $PID2
	sleep 1
	python client.py 
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1 $PID2
	#kill the pyro nameserver daemon
	pkill pyro4-ns
popd
retval=$retval || $ret

pushd Example03
	echo $PWD
	gcc -o application3 application3.c
	python Example03.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example04
	echo $PWD
	python Example04.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example05
	echo $PWD
	python Example05.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

##
## TODO: run local ssh server with paramiko and test-ping that one
##
#pushd PingTest
#	echo $PWD
#	ssh -n mmp@mech.fsv.cvut.cz "bash -c \"cd mupif-code/examples/PingTest;python ctu-server.py& sleep 10; pkill \"python ctu-server.py\"\"" &
#	sleep 1
#	python test.py 
#	ret=$?
#	(( retval=$retval || $ret ))
#	echo "=================== Exit status $?"
#popd

echo "*** Global return status $retval"
echo "*** Bye."

exit $retval


