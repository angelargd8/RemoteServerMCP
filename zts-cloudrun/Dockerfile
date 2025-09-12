FROM node:18-alpine
RUN apk add --no-cache git bash dos2unix
WORKDIR /app
RUN git clone --recurse-submodules https://github.com/zotero/translation-server . \
 && npm ci
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh
EXPOSE 1969
CMD ["/app/start.sh"]
