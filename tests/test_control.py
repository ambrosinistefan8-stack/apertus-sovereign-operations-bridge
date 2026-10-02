import unittest
from app.apertus_client import MockApertusClient
from app.fixtures import scenario_documents
from app.service import run_workflow

class ControlFlowTests(unittest.TestCase):
    def run_case(self,s):
        return run_workflow(MockApertusClient(),"Prepare the correct customer response.",scenario_documents(s),["product","price_chf","delivery_days"])
    def test_normal_verified(self): self.assertEqual(self.run_case("normal")["status"],"VERIFIED")
    def test_missing_requires_review(self): self.assertEqual(self.run_case("missing")["status"],"HUMAN_REVIEW")
    def test_conflict_requires_review(self): self.assertEqual(self.run_case("conflict")["status"],"HUMAN_REVIEW")
    def test_untrusted_instruction_blocks(self): self.assertEqual(self.run_case("untrusted")["status"],"BLOCKED")
    def test_protected_action_requires_review(self): self.assertEqual(self.run_case("human_gate")["status"],"HUMAN_REVIEW")

if __name__=="__main__": unittest.main()
