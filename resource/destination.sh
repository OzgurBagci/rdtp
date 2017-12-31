!/bin/sb

python3.6 -c "from source.rdtp import destinationwrapper;
 destinationwrapper.wrap_destination(['10.10.4.2', '10.10.2.2']);
"
