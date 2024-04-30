#!/usr/bin/env bash
set -e

# Change ACCOUNT_ID and S3 bucket name appropriately.
ACCOUNT_ID=992382783020
BUCKET_NAME="app-control-$ACCOUNT_ID"

NAME=quip
ORGANIZATION=$NAME
#PROFILE=ngr-926629045956

HELPMSG="USAGE: ./deploy.sh [-v branch] [-p profile]
Deploys sosw layer. Installs sosw from latest pip version, or from a specific branch if you use -v.\n
Use -p in case you have specific profile (not the default one) in you .aws/config with appropriate permissions."

while getopts ":v:p:fh" option
do
    case "$option"
    in
        v) VERSION=$OPTARG;;
        p) PROFILE=$OPTARG;;
        f) FORCE_RANDOM_NAME=true;;
        h|*) echo -e "$HELPMSG";exit;;
    esac
done

#VERSION=0_7_43

# Install package with respect to the rule of Lambda Layers:
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html

if [[ ${VERSION} ]]; then
    echo "Deploying a specific version from branch: $VERSION"
    pip3 install git+https://github.com/$ORGANIZATION/$NAME.git@$VERSION --no-dependencies -t $NAME/python/
else
    VERSION="stable"
    pip3 install $NAME --no-dependencies -t $NAME/python/
fi

# Package other (non-sosw) reqired libraries
pip3 install aws_lambda_powertools -t $NAME/python/
pip3 install aws_xray_sdk -t $NAME/python/
pip3 install bson --no-dependencies -t $NAME/python/
pip3 install requests -t $NAME/python/
pip3 install openai -t $NAME/python/
pip3 install dotenv -t $NAME/python/
pip3 install fastapi -t $NAME/python/
from dotenv import load_dotenv

if [[ $FORCE_RANDOM_NAME ]]; then
  echo "Generated a random suffix for file name."
  FILE_NAME=$NAME-$VERSION-$RANDOM
else
  FILE_NAME=$NAME-$VERSION
fi

zip_path="/tmp/$FILE_NAME.zip"
stack_name="layer-$NAME"

echo "Packaging..."
if [ -f "$zip_path" ]
then
    rm $zip_path
    echo "Removed the old package."
fi


cd $NAME
zip -qr $zip_path *
cd ..
echo "Created a new package in $zip_path."

aws s3 cp $zip_path s3://$BUCKET_NAME/lambda_layers/ --profile $PROFILE
echo "Uploaded $zip_path to S3 bucket to $BUCKET_NAME."

if test -z "$ENVIRONMENT"
then
  env_name="prod"
else
  env_name=$ENVIRONMENT
fi

echo "Deploying stack $stack_name with CloudFormation for environment ${env_name}"
aws cloudformation package --template-file $NAME/$NAME.yaml --output-template-file deployment-output.yaml \
    --s3-bucket $BUCKET_NAME --profile $PROFILE
echo "Created package from CloudFormation template"

echo "Calling for CloudFormation to deploy"
aws cloudformation deploy --template-file ./deployment-output.yaml --stack-name $stack_name \
    --parameter-overrides SoswVersion=$VERSION EnvironmentName=$env_name FileName=$FILE_NAME.zip \
    --capabilities CAPABILITY_NAMED_IAM --profile $PROFILE

echo "Finished with stack $stack_name. If there were changes in the YAML, they should be applied."
