import json,sys
from app.apertus_client import MockApertusClient
from app.fixtures import scenario_documents
from app.service import run_workflow

scenario=sys.argv[1] if len(sys.argv)>1 else "normal"
result=run_workflow(MockApertusClient(),"Prepare the correct customer response.",scenario_documents(scenario),["product","price_chf","delivery_days"])
print(json.dumps(result,ensure_ascii=False,indent=2))
