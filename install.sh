#!/bin/bash

strAddress=
strToken=

usage()
{
	cat << EOT

Usage :  ${0} [OPTION] ...
  install client

Options:
  --token 		token string
  --address 	server address
EOT
}

while [[ true ]]; do
	case "$1" in
		--token )
			strToken=$2
			shift 2
			;;
		--address )
			strAddress=$2
			shift 2
			;;
		--help )
			usage
			exit 0
			;;
		* )
			usage
			exit 1
			;;
	esac
	if [[ $# == 0 ]]; then
		break
	fi
done

if [[ "$strAddress" == "" ]]; then
	strAddress="xd.zhexi.tech"
fi

if [[ "$strToken" == "" ]]; then
	echo token cannot be empty
	exit 1
fi

if [[ $UID -ne 0 ]]; then
	echo "Superuser privileges are required to run this script."
	exit 1
fi

sysType=$(uname -s)
if [[ "$sysType" == "Darwin" ]]; then
	sysType="darwin-amd64"
elif [[ "$sysType" == "Linux" ]]; then
		sysType="linux-amd64"
		archType=$(uname -m)
		if [[ $archType == aarch64 ]] ;
		then
		    sysType="linux-arm64"
		elif  [[ $archType == arm* ]] ;
		then
			sysType="linux-arm"
		elif  [[ $archType == i*86 ]] ;
		then
			sysType="linux-386"
		fi
fi
echo "system type is $sysType"

echo "start to download client"
curl -o csclient http://$strAddress/upgrade/$sysType/csclient
if [[ $? -ne 0 ]]; then
	# curl not found, try wget download
    wget -O csclient http://$strAddress/upgrade/$sysType/csclient
fi
chmod +x csclient
echo "start to install"
./csclient install -token $strToken -address $strAddress
