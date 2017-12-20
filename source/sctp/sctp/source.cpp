#include <string>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/sctp.h>
#include <arpa/inet.h>


int main(int argc, std::string s_ips[], std::string d_ips[], int port)
{
	int my_sctp = socket(PF_INET, SOCK_SEQPACKET, IPPROTO_SCTP);
	struct sockaddr_in servaddr[sizeof(s_ips) / sizeof(s_ips[0])];
	int i = 0;
	for(i = 0; i < sizeof(s_ips) / sizeof(s_ips[0]); i++)
	{
		struct sockaddr_in serveradd;
		bzero((void *) &serveradd, sizeof(serveradd));
		serveradd.sin_family = AF_INET;
		inet_pton(AF_INET, s_ips[i].c_str(), &serveradd.sin_addr);
		serveradd.sin_port = htons(port);
		servaddr[i] = serveradd;
	}
	sctp_bindx(my_sctp, (struct sockaddr*) &servaddr, i + 1, SCTP_BINDX_ADD_ADDR);
	struct sockaddr_in destaddr[sizeof(d_ips) / sizeof(d_ips[0])];
	for (i = 0; i < sizeof(d_ips) / sizeof(d_ips[0]); i++)
	{
		struct sockaddr_in destadd;
		bzero((void *) &destadd, sizeof(destadd));
		destadd.sin_family = AF_INET;
		inet_pton(AF_INET, d_ips[i].c_str(), &destadd.sin_addr);
		destadd.sin_port = htons(port);
		destaddr[i] = destadd;
	}
	sctp_assoc_t assoc_id = 0;
	sctp_connectx(my_sctp, (struct sockaddr*) &destaddr, i + 1, &assoc_id);
	return 0;
}
