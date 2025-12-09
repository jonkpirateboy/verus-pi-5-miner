#!/usr/bin/env bash

LOG=/tmp/verus_raw.log
HASHFILE=/tmp/verus_hashrate.log
SHAREFILE=/tmp/verus_shares.log

: > "$HASHFILE"
echo "0,0" > "$SHAREFILE"

tail -F "$LOG" | while read -r line; do
    # Example line:
    # [time] accepted: 6/6 (diff ...), 3761.95 kH/s yes!
    if [[ "$line" =~ accepted:\ ([0-9]+)/([0-9]+).*,\ ([0-9]+\.[0-9]+)\ kH/s\ yes! ]]; then
        acc="${BASH_REMATCH[1]}"
        tot="${BASH_REMATCH[2]}"
        khs="${BASH_REMATCH[3]}"

        echo "$khs" > "$HASHFILE"
        echo "$acc,$tot" > "$SHAREFILE"
    fi
done
