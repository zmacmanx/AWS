import logging
import boto3
import json
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)



def lambda_handler(event, context):
    conf = boto3.client('config')
    sns = boto3.client('sns')
    
    logger.info('got event{}'.format(event))
    
    evObj = json.loads(event['invokingEvent'])
    rules = json.loads(event['ruleParameters'])

    compliant = 'COMPLIANT'
    annotation = 'Asset is compliant';
    
    try:
        if len(rules):
            for tag in rules:
                if tag in evObj['configurationItem']['tags'].keys():
                    matchedObject = re.match(rules[tag], evObj['configurationItem']['tags'][tag])
                    if not matchedObject:
                        compliant = 'NON_COMPLIANT'
                        annotation = 'The pattern did not match the requirements'
                else:
                    compliant = 'NON_COMPLIANT'
                    annotation = 'Required tag is missing from the asset'
        else:
            compliant = 'NOT_APPLICABLE'
            annotation = 'No tag requirement is defined'

        response = conf.put_evaluations(
            Evaluations=[
                {
                    'ComplianceResourceType': evObj['configurationItem']['resourceType'],
                    'ComplianceResourceId': evObj['configurationItem']['resourceId'],
                    'ComplianceType': compliant,
                    'Annotation': str(annotation),
                    'OrderingTimestamp': evObj['notificationCreationTime']
                },
            ],
            ResultToken=event['resultToken'],
            TestMode=False
        )
        
        '''
        response = sns.publish(
            TopicArn='<ADD YOUR SNS TOPIC ARN HERE!!!!',
            Message='Config Evaluation Result: ' +  
            evObj['configurationItem']['resourceId'] + 
                ' (' + evObj['configurationItem']['resourceType'] + ') is ' + 
                compliant + ' (' + annotation + ')',
            Subject='Config Evaluation'
        )
        '''
    except Exception as e:
        logger.error('Exception reading input tags, event{}'.format(event))
        raise e
    
    return 'Configuration check complete'
