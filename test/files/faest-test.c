#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdbool.h>
#include "api.h"

int run_test(bool verbose) {
    if (verbose) {
        printf("Variant: %s\n", CRYPTO_ALGNAME);
        printf("Generating Keypair..");
    }
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    unsigned char sk[CRYPTO_SECRETKEYBYTES];
    if (crypto_sign_keypair(pk, sk)) {
        fprintf(stderr, "Error creating keypair\n");
        return 1;
    }
    if (verbose) {
        printf(" Success!\n");
        printf("Signing..");
    }
    const unsigned char *m = "This is the message to sign.";
    size_t mlen = strlen(m);
    unsigned char sm[CRYPTO_BYTES + mlen];
    size_t smlen;
    if (crypto_sign(sm, &smlen, m, mlen, sk)) {
        fprintf(stderr, "Error signing\n");
        return 1;
    }
    if (verbose) {
        printf(" Success!\n");
        printf("Verifying..");
    }
    unsigned char open_m[mlen];
    strncpy(open_m, m, mlen);
    size_t open_mlen;

    if (crypto_sign_open(open_m, &open_mlen, sm, smlen, pk)) {
        fprintf(stderr, "Error verifying\n");
        return 1;
    }
    if (verbose) {
        printf(" Success!\n");
    }

    return 0;
}

int main(int argc, char *argv[]) {
    return run_test(false);
    /*
    if (argc != 2)
        return run_test(true);

    int repeats = atoi(argv[1]);
    while (repeats-- > 0) {
        if (run_test(false))
            return 1;
    }
    */

    return 0;
}
