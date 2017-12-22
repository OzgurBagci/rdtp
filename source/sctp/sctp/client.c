#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/sctp.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>

int main(int argv, char args[], char filename[]) {

	if (filename == "" || args == "") return -1;

	int sock;
	if((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_SCTP)) == -1){
		return -1;
	}

	struct sctp_initmsg initmsg;
	memset(&initmsg, 0, sizeof(initmsg));
	initmsg.sinit_num_ostreams = 3;
	initmsg.sinit_max_instreams = 3;
	initmsg.sinit_max_attempts = 2;
	setsockopt(sock, IPPROTO_SCTP, SCTP_INITMSG, &initmsg, sizeof(initmsg));

	struct addrinfo *res, hints;
	hints.ai_family = AF_INET;
	hints.ai_protocol = IPPROTO_SCTP;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_ADDRCONFIG | AI_V4MAPPED;

	
	char running[512]; 
	strncpy(running, args, strlen(args));
	while (running != "")
	{
		char * token = strtok(running, ":");
		getaddrinfo(token, "1234", &hints, &res);
	}
	
	

	struct sockaddr_storage *connect = NULL;
	int cc = 0, count = 0;
	for(; res; res = res->ai_next){
		connect = realloc(connect, cc + res->ai_addrlen);
		memcpy((char*)connect + cc, res->ai_addr, res->ai_addrlen);
		count++;
		cc += res->ai_addrlen;
	}
	if(sctp_connectx(sock, (struct sockaddr*)connect, count, 0) == -1){ 
		exit(-1);
	}
	char *myfilename = strrchr(filename, '/');
	myfilename = myfilename + 1;

	sctp_sendmsg(sock, (void*)myfilename, (size_t)strlen(myfilename), NULL, 0, 0, 0, 0, 0, 0);
	unsigned char buffer[512];
	size_t bytesRead = 0;
	FILE *myfile = fopen(filename, "rb");
	if(myfile != NULL)
	{
		while((bytesRead = fread(buffer, sizeof(buffer), 1, myfile)) > 0)
		{
			sctp_sendmsg(sock, (void*)buffer, (size_t)strlen(buffer), NULL, 0, 0, 0, 0, 0, 0);
		}
	}
	fclose(myfile);
	char *endmessage = (char*) malloc(sizeof(char) * 2);
	endmessage[0] = EOF;
	endmessage[1] = '\0';
	sctp_sendmsg(sock, (void*)endmessage, (size_t)strlen(endmessage), NULL, 0, 0, 0, 0, 0, 0);
	close(sock);
	
	return 0;
}
