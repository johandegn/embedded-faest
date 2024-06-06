#include "faest_test.h"

int main(void) {
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    if (read_pk(pk) == 1)
        return 1;

    unsigned char sm[CRYPTO_BYTES + MSG_LEN];

    if (read_signature(sm) == 1)
        return 1;

    unsigned char open_m[MSG_LEN] = MSG;
    unsigned long open_mlen; // TODO: change to size_t again

    if (crypto_sign_open(open_m, &open_mlen, sm, CRYPTO_BYTES + MSG_LEN, pk) == -1)
        return 1;

    return 0;
}
