import uuid
import pandas as pd
from datetime import datetime
from vertexai.preview.evaluation import EvalTask
from vertexai.preview.evaluation.metrics import (
    PointwiseMetricPromptTemplate,
    PointwiseMetric,
    TrajectorySingleToolUse,
)
from utils import save_evaluation_results, print_evaluation_summary, get_agent_response

# Custom metric for outlier detection accuracy
outlier_detection_metric = PointwiseMetric(
    metric="outlier_detection_metric",
    metric_prompt_template=PointwiseMetricPromptTemplate(
        instruction="""You are an expert evaluator assessing an AI's ability to correctly identify and explain insurance claim outliers.""",
        criteria={
            "Detection Accuracy": """The AI should correctly identify outlier claims based on business rules and provide clear explanations.""",
            "Interpretability": """The explanation should clearly show the mechanistic reasoning behind outlier flags."""
        },
        rating_rubric={
            "5": "Excellent: Perfect outlier identification with clear mechanistic interpretability",
            "3": "Good: Mostly correct with minor explanation issues", 
            "1": "Poor: Incorrect detection or unclear reasoning"
        },
        input_variables=["prompt", "reference", "response"],
    ),
)

factual_accuracy_metric = PointwiseMetric(
    metric="factual_accuracy_metric",
    metric_prompt_template=PointwiseMetricPromptTemplate(
        instruction="""You are an expert evaluator assessing the factual accuracy of an AI's answer to a user's question, given a natural language prompt and a 'reference' (ground truth) answer. Your task is to determine if all factual information in the AI's answer is precise and correct when compared to the reference.""",
        criteria={
            "Accuracy": """The AI's answer must present factual information (numerical values, names, dates, specific values) that are **identical** to or an exact logical derivation from the reference.
           - **Wording may vary, but the core factual information must be the same.**
           - No numerical discrepancies.
           - No incorrect names or identifiers.
           - No fabricated or misleading details.
           - Note: Minor rounding of numerical values that doesn't alter the core meaning or lead to significant misrepresentation is generally acceptable, assuming the prompt doesn't ask for exact precision."""
        },
        rating_rubric={
            "5": "Excellent: The response is entirely factually correct. **All factual information precisely matches the reference.** There are absolutely no inaccuracies or misleading details.",
            "3": "Good: The response is generally accurate, but contains minor, non-critical factual inaccuracies (e.g., a negligible rounding difference or slightly wrong detail) that do not impact the core understanding.",
            "1": "Poor: The response contains significant factual errors, major numerical discrepancies, or fabricated information that makes the answer incorrect or unreliable."
        },
        input_variables=["prompt", "reference", "response"],
    ),
)

completeness_metric = PointwiseMetric(
    metric="completeness_metric",
    metric_prompt_template=PointwiseMetricPromptTemplate(
        instruction="""You are an expert evaluator assessing the completeness of an AI's answer to a user's question, given a natural language prompt and a 'reference' (ground truth) answer. Your task is to determine if the AI's answer provides all the essential information requested by the user and present in the reference.""",
        criteria={
            "Completeness": """The AI's answer must include **all** key pieces of information explicitly or implicitly requested by the prompt and present in the reference.
           - No omissions of critical facts.
           - All requested attributes (e.g., age AND email, not just one) must be present.
           - If the reference provides a multi-part answer, all parts must be covered."""
        },
        rating_rubric={
            "5": "Excellent: The response is perfectly complete. **All key information requested by the prompt and present in the reference is included.** There are absolutely no omissions.",
            "3": "Good: The response is mostly complete. It has only a slight, non-critical omission that does not impact the core understanding or utility of the answer.",
            "1": "Poor: The response is critically incomplete. Essential parts of the requested information are missing, making the answer less useful or unusable for the user's purpose."
        },
        input_variables=["prompt", "reference", "response"],
    ),
)

# CRITICAL FIX: Add the missing trajectory metric
tool_use_metric = TrajectorySingleToolUse(tool_name="list_table_ids")

def run_eval():
    eval_dataset = pd.read_json("evaluation_dataset.json")

    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    experiment_run_id = f"{current_time}-{uuid.uuid4().hex[:8]}"

    print(f"--- Starting insurance claims evaluation: ({experiment_run_id}) ---")

    eval_task = EvalTask(
        dataset=eval_dataset,
        metrics=[
            outlier_detection_metric,
            factual_accuracy_metric,
            completeness_metric,
            tool_use_metric,  # NOW INCLUDED - this fixes the trajectory error
        ],
        experiment="evaluate-insurance-claims-agent"
    )

    try:
        eval_result = eval_task.evaluate(
            runnable=get_agent_response, experiment_run_name=experiment_run_id
        )
        save_evaluation_results(eval_result, experiment_run_id)
        print_evaluation_summary(eval_result)

    except Exception as e:
        print(f"An error occurred during evaluation run: {e}")

if __name__ == "__main__":
    run_eval()