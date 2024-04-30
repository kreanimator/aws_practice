#!/usr/bin/env bash
set -e

# Change ACCOUNT_ID and S3 bucket name appropriately.
ACCOUNT_ID=926629045956
BUCKET_NAME=app-control-$ACCOUNT_ID
NAME=ddb_models
REPOSITORY=fs-lambdas
REPOSITORY_PATH=ssh://git-codecommit.us-west-2.amazonaws.com/v1/repos/fs-lambdas
PROFILE=ngr-926629045956

HELPMSG="USAGE: ./deploy.sh [-n name] [-r full url of the repository] [-p profile]
Deploys 'ddb-models' layer. Use -p in case you have specific profile (not the default one)
in you .aws/config with appropriate permissions.
NAME parameter should not contain _ characters"

while getopts ":n:p:r:h" option
do
    case "$option"
    in
        n) NAME=$OPTARG;;
        p) PROFILE=$OPTARG;;
        r) REPOSITORY_PATH=$OPTARG;REPOSITORY=`echo $OPTARG | awk '$!_=$-_=$NF' FS='[/]'`;;
        h|*) echo -e "$HELPMSG";exit;;
    esac
done

STACK_NAME="layer-`echo $NAME | sed s/_/-/g`"

echo "REPOSITORY_PATH=$REPOSITORY_PATH"
echo "REPOSITORY=$REPOSITORY"
echo "PROFILE=$PROFILE"
echo "NAME=$NAME"

rm -rf /tmp/$REPOSITORY
rm -rf /tmp/$NAME.zip
rm -rf /tmp/$NAME-stable.zip
rm -rf /tmp/layer-$NAME
echo "Cleaned old artifacts from /tmp"

git clone $REPOSITORY_PATH /tmp/$REPOSITORY
cd /tmp/$REPOSITORY
mkdir -p /tmp/layer-$NAME/python
cp -r $NAME /tmp/layer-$NAME/python/
cd /tmp/layer-$NAME
zip -r /tmp/$NAME-stable.zip *
cd /tmp/
unzip -l /tmp/$NAME-stable.zip
MD5=`cat /tmp/layer-$NAME/python/ddb_models/*.py | md5`
echo "Created a new package in /tmp/$NAME-stable.zip with MD5 of Python files: $MD5"

aws s3 cp /tmp/$NAME-stable.zip s3://$BUCKET_NAME/lambda_layers/ --profile $PROFILE
echo "Uploaded $NAME-stable.zip to S3 bucket to $BUCKET_NAME."

echo "Deploying stack $NAME with CloudFormation"
pwd
aws cloudformation package --template-file /Users/ngr/Programming/fs-cf-infrastructure/layers/$NAME/template.yaml \
    --output-template-file deployment-output.yaml --s3-bucket $BUCKET_NAME --profile $PROFILE
echo "Created package from CloudFormation template"

echo "Calling for CloudFormation to deploy"
aws cloudformation deploy --template-file ./deployment-output.yaml --stack-name $STACK_NAME \
    --parameter-overrides FileName=$NAME-stable.zip PackageMD5=$MD5 \
    --capabilities CAPABILITY_NAMED_IAM --profile $PROFILE

echo "Finished with stack $stack_name. If there were changes in the YAML, they should be applied."
