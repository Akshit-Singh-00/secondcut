FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
COPY requirements.lock.txt ${LAMBDA_TASK_ROOT}/requirements.lock.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -c ${LAMBDA_TASK_ROOT}/requirements.lock.txt
COPY secondcut ${LAMBDA_TASK_ROOT}/secondcut
COPY static ${LAMBDA_TASK_ROOT}/static
ENV SECONDCUT_DATA=/tmp/secondcut SECONDCUT_DEPLOYMENT=aws-lambda
CMD ["secondcut.lambda_handler.handler"]
