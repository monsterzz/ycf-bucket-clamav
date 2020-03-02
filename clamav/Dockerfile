FROM python:3.7-stretch AS build

RUN apt-get update -qq && apt-get install build-essential libjson-c-dev -y
ADD https://www.clamav.net/downloads/production/clamav-0.102.2.tar.gz /clamav.tgz
RUN mkdir -p /clamav && tar -C /clamav --strip-components 1 -xzf /clamav.tgz

WORKDIR /clamav
RUN ./configure --enable-static --with-libjson
RUN make

FROM python:3.7-stretch
COPY --from=build /clamav/clamscan/.libs/clamscan /clamav/clamscan
COPY --from=build /clamav/libclamav/.libs/libclamav.so.9 /clamav/libclamav.so.9
COPY --from=build /clamav/libclamav/.libs/libclammspack.so.0 /clamav/libclammspack.so.0
COPY --from=build /clamav/libclamav/.libs/libclamunrar_iface.so /clamav/libclamunrar_iface.so
COPY --from=build /lib/x86_64-linux-gnu/libjson-c.so.3 /clamav/libjson-c.so.3
COPY --from=build /usr/lib/x86_64-linux-gnu/libltdl.so.7 /clamav/libltdl.so.7