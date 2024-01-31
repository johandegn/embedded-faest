#include "faest_test.h"

int main(void) {
    unsigned char sk[CRYPTO_SECRETKEYBYTES];
    if (read_sk(sk) == 1)
        return 1;

    unsigned char sm[CRYPTO_BYTES + MSG_LEN];
    unsigned long long smlen; // TODO: change to size_t again
    if (crypto_sign(sm, &smlen, MSG, MSG_LEN, sk) == -1)
        return 1;

    return write_signature(sm);
}
