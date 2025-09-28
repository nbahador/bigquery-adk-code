import json
import os
import asyncio
import run_agent
import numbers
import math


def get_agent_response(prompt: str) -> dict:
   """Invokes the agent with a prompt and returns its response."""

   try:
       response = asyncio.run(run_agent.run_conversation(prompt))  # Invoke the agent
       return response
   except Exception as e:
       return {"response": "Error: Agent failed to produce a response."}


def save_evaluation_results(eval_result, experiment_run):
   """Processes, saves, and prints the evaluation results for a single run."""

   os.makedirs("eval_results", exist_ok=True)
   output_file_path = os.path.join(
       "eval_results", f"bq_agent_eval_results_{experiment_run}.json"
   )

   # Prepare data for JSON serialization
   eval_result_dict = {
       "summary_metrics": eval_result.summary_metrics,
       "pointwise_metrics": eval_result.metrics_table.to_dict("records"),
   }
   # --- Save the results as a JSON file ---
   with open(output_file_path, "w") as f:
       json.dump(eval_result_dict, f, indent=4)
   print(f"Results for run '{experiment_run}' saved to {output_file_path}")


def print_evaluation_summary(eval_result):
   """Prints a detailed summary of the evaluation results, including summary-level and aggregated pointwise metrics."""
  
   pointwise_metrics = eval_result.metrics_table
   # Print summary metrics for the current run
   summary_metrics = eval_result.summary_metrics
   if summary_metrics:
       for key, value in summary_metrics.items():
           if isinstance(value, numbers.Real) and not math.isnan(value):
               value = f"{value:.2f}"

           metric_name = key.replace("/mean", "").replace("_", " ").title()
           print(f"- {metric_name}: {key}: {value}")
   else:
       print("No summary metrics found for this run.")
   print("\n" + "=" * 50 + "\n")

   if not pointwise_metrics.empty:
       total_questions = len(pointwise_metrics)
       avg_completeness_score = pointwise_metrics["completeness_metric/score"].mean()
       avg_factual_accuracy_score = pointwise_metrics[
           "factual_accuracy_metric/score"
       ].mean()
       print("\n" + "=" * 50 + "\n")
       print("--- Aggregated Evaluation Summary ---")
       print(f"Total questions in evaluation dataset: {total_questions}")
       print(f"Average Completeness Score: {avg_completeness_score:.2f}")
       print(f"Average Factual Accuracy Score: {avg_factual_accuracy_score:.2f}")
       print("\n" + "=" * 50 + "\n")
   else:
       print("\nNo successful evaluation runs were completed.")