#!/bin/bash
# First-boot script (Terraform fills in ${repo_url}).
# Log: /var/log/user-data.log  (view via Session Manager or EC2 "Get system log")
set -euxo pipefail
exec > /var/log/user-data.log 2>&1

apt-get update
apt-get install -y docker.io docker-compose-v2 git
systemctl enable --now docker

git clone ${repo_url} /opt/geoclock-api
cd /opt/geoclock-api

docker compose up -d --build

# Wait for the API container, then create/upgrade the database tables.
for i in $(seq 1 30); do
  if docker compose exec -T api flask db upgrade; then
    break
  fi
  sleep 5
done
