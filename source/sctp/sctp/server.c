#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/sctp.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>

int main(int argc, char *argv[]){

	if (argc != 2)
	{
		return -1;
	}

	char *args = argv[1];

	struct sockaddr_in client;
	int sock;
	if((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_SCTP)) == -1){
		return -1;
	}

	struct sctp_initmsg initmsg;
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
	running[strlen(args)] = '\0';
	char * token = strtok(running, ":");
	while (token != NULL)
	{
		getaddrinfo(token, "1234", &hints, &res);
		token = strtok(NULL, ":");
	}

	struct sockaddr_storage *connect = NULL;
	int cc = 0, count = 0;
	for(; res; res = res->ai_next){
		connect = realloc(connect, cc + res->ai_addrlen);
		memcpy((char*)connect + cc, res->ai_addr, res->ai_addrlen);
		count++;
		cc += res->ai_addrlen;
	}
	if(sctp_bindx(sock, (struct sockaddr*)connect, count, SCTP_BINDX_ADD_ADDR) == -1){
		return -1;
	}
	if(listen(sock,5)==-1){
		return -1;
	}
	int newsock;
	char buffer[512];
	int clnlen = sizeof(client), flags;
	if((newsock = accept(sock, (struct sockaddr*)&client, &clnlen)) == -1){
		return -1;
	}

	while(1)
	{
		memset(&buffer, '\0', sizeof(buffer));
		struct sctp_sndrcvinfo sndrcvinf;
		sctp_recvmsg(newsock, (void*)buffer, sizeof(buffer), (struct sockaddr*)NULL, 0, &sndrcvinf, &flags);
		if (buffer[0] != '\0') break;
	}
	FILE *myfile = fopen(buffer, "wb");
	while(1){
		memset(&buffer, '\0', sizeof(buffer));
		struct sctp_sndrcvinfo sndrcvinfo;
		sctp_recvmsg(newsock, (void*)buffer, sizeof(buffer), (struct sockaddr*)NULL, 0, &sndrcvinfo, &flags);
		if (buffer[strlen(buffer) - 1] == EOF)
		{
			fwrite(&buffer, 1, (strlen(buffer) - 1) * sizeof(char), myfile);
			break;
		};
		fwrite(&buffer, 1, strlen(buffer) * sizeof(char), myfile);
	}
	fclose(myfile);
	close(newsock);
	close(sock);
	return 0;
}
