
[> Liteeth 16-byte bug demonstration
------------------------------------
Build and flash the image with:

```sh
$ ./colorlite.py --ip-address=192.168.1.20 --flash
```

Then run the echo client:

```sh
$ ./echo.py --ip-address=192.168.1.20 --packet-length 16
```

This shows only single packet is echod back by liteeth. Running it with a different
`--packet-length` works without issues.
