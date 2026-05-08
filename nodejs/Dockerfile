FROM node:24.2.0-alpine AS base
WORKDIR /app
COPY . .
RUN npm i --no-audit \
	&& npm run build


FROM node:24.2.0-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=base /app .
COPY data/references.json /app/data/references.json
RUN rm -Rf node_modules/ \
  && npm ci --ignore-scripts \
  && rm -rf Dockerfile src/ .dockerignore package-lock.json \
  && mv dist/* . \
  && rmdir dist/
CMD ["node", "main/server.js"]

