FROM node:12-buster

EXPOSE 3000
WORKDIR /usr/src/epub-press

COPY package.json package-lock.json ./
RUN npm install --production

# Automatically downloads and installs Calibre. To use Kindlegen instead, set ARG converter=kindlegen.
ARG converter=calibre
ENV CONVERSION_BACKEND=$converter
RUN if [ "$converter" = "calibre" ] ; then apt-get update && apt-get install -y libgl1-mesa-glx libc6 calibre; fi


COPY . .

CMD ["npm", "run", "start:docker"]
