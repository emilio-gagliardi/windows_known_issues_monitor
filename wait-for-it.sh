#!/bin/sh

# wait-for-it.sh: wait for a service to be available
# Usage: wait-for-it.sh host:port [-t timeout] [-- command args]

set -e

TIMEOUT=15
QUIET=0

echoerr() {
  if [ "$QUIET" -ne 1 ]; then printf "%s\n" "$*" 1>&2; fi
}

usage() {
  echoerr "Usage: $0 host:port [-t timeout] [-- command args]"
  exit 1
}

wait_for() {
  for i in `seq $TIMEOUT` ; do
    nc -z "$HOST" "$PORT" > /dev/null 2>&1
    
    result=$?
    if [ $result -eq 0 ] ; then
      if [ $# -gt 0 ] ; then
        exec "$@"
      fi
      exit 0
    fi
    sleep 1
  done
  echo "Operation timed out" >&2
  exit 1
}

while [ $# -gt 0 ]
do
  case "$1" in
    *:* )
    HOST=$(printf "%s\n" "$1"| cut -d : -f 1)
    PORT=$(printf "%s\n" "$1"| cut -d : -f 2)
    shift 1
    ;;
    -t)
    TIMEOUT="$2"
    if [ "$TIMEOUT" = "" ]; then break; fi
    shift 2
    ;;
    --)
    shift
    break
    ;;
    --help)
    usage
    ;;
    *)
    echoerr "Unknown argument: $1"
    usage
    ;;
  esac
done

if [ "$HOST" = "" -o "$PORT" = "" ]; then
  echoerr "Error: you need to provide a host and port to test."
  usage
fi

wait_for "$@"
