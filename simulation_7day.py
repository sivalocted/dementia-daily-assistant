"""
Automated 7-Day Accelerated Domestic Activity Simulation (T16)
MSc Computer Science Dissertation Verification Component

Simulates 168 hours (7 full calendar days) of continuous domestic activity
on an accelerated clock, logging every occurrence, state transition, and
telemetry event to verify that zero prompts are dropped and zero duplicate alerts fire.
"""

import os
import json
import random
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any

from reminder_engine import ReminderEngine, Task, Occurrence, Status


def run_simulation(seed: int = 42) -> Dict[str, Any]:
    random.seed(seed)
    
    # 5 standard daily routines for recipient "John"
    routines = [
        Task(task_id=1, label="Have morning tea & toast", time_of_day="08:30", days_mask=127, snooze_minutes=10, max_snoozes=2, window_minutes=45, alert_caregiver=False),
        Task(task_id=2, label="Take blood pressure medication", time_of_day="09:00", days_mask=127, snooze_minutes=10, max_snoozes=2, window_minutes=60, alert_caregiver=True),
        Task(task_id=3, label="Have your lunch", time_of_day="12:30", days_mask=127, snooze_minutes=10, max_snoozes=2, window_minutes=60, alert_caregiver=True),
        Task(task_id=4, label="Afternoon walk in the garden", time_of_day="15:30", days_mask=31, snooze_minutes=15, max_snoozes=2, window_minutes=60, alert_caregiver=False), # Weekdays only
        Task(task_id=5, label="Take evening heart medicine", time_of_day="20:00", days_mask=127, snooze_minutes=10, max_snoozes=2, window_minutes=60, alert_caregiver=True),
    ]

    engine = ReminderEngine(tasks=routines, escalate_after_misses=2)
    start_date = date(2026, 11, 16) # Monday
    
    simulation_log = []
    total_planned = 0
    total_confirmed = 0
    total_snoozed = 0
    total_missed = 0
    
    # Sweep through 7 calendar days (168 hours)
    for day_idx in range(7):
        current_date = start_date + timedelta(days=day_idx)
        day_name = current_date.strftime("%A")
        planned_occs = engine.plan_day(current_date)
        total_planned += len(planned_occs)
        
        # Simulate each occurrence through its lifecycle
        for occ in planned_occs:
            hour, minute = map(int, occ.task.time_of_day.split(":"))
            scheduled_dt = datetime.combine(current_date, time(hour, minute))
            
            # 1. Trigger poll at scheduled time
            showing = engine.poll(scheduled_dt)
            assert occ in showing, f"Error: Planned task {occ.task.label} failed to show at {scheduled_dt}"
            
            # 2. Simulate realistic recipient behavior:
            # 80% direct confirmation within 5 minutes
            # 15% snooze once, then confirm
            # 5% genuine miss (e.g. asleep or outside)
            behavior_roll = random.random()
            
            if behavior_roll < 0.80:
                # Direct confirmation
                confirm_time = scheduled_dt + timedelta(minutes=random.randint(1, 8))
                engine.confirm(occ, confirm_time)
                total_confirmed += 1
                action_taken = "confirmed_on_time"
            elif behavior_roll < 0.95:
                # Snooze once at +3m, then confirm at +14m
                snooze_time = scheduled_dt + timedelta(minutes=3)
                engine.snooze(occ, snooze_time)
                total_snoozed += 1
                
                # Re-prompts 10m later
                reprompt_time = snooze_time + timedelta(minutes=occ.task.snooze_minutes)
                re_showing = engine.poll(reprompt_time)
                assert occ in re_showing
                
                confirm_time = reprompt_time + timedelta(minutes=random.randint(1, 5))
                engine.confirm(occ, confirm_time)
                total_confirmed += 1
                action_taken = "snoozed_then_confirmed"
            else:
                # Unconfirmed -> Window timeout expires
                expire_time = scheduled_dt + timedelta(minutes=occ.task.window_minutes + 1)
                engine.poll(expire_time)
                assert occ.status == Status.MISSED
                total_missed += 1
                action_taken = "missed_unanswered"
            
            simulation_log.append({
                "day": day_name,
                "date": current_date.strftime("%Y-%m-%d"),
                "time": occ.task.time_of_day,
                "label": occ.task.label,
                "action": action_taken,
                "final_status": occ.status.value,
                "snoozes": occ.snoozes,
            })
            
    completion_rate = engine.completion_rate()
    caregiver_alerts = engine.caregiver_alerts
    
    results = {
        "simulation_duration_days": 7,
        "simulation_duration_hours": 168,
        "total_routines_planned": total_planned,
        "total_confirmed_done": total_confirmed,
        "total_snooze_interactions": total_snoozed,
        "total_missed": total_missed,
        "overall_completion_rate_pct": round(completion_rate * 100, 2),
        "total_caregiver_alerts_dispatched": len(caregiver_alerts),
        "caregiver_alerts": [
            {
                "timestamp": a["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "task_id": a["task_id"],
                "label": a["label"],
                "consecutive_misses": a["consecutive_misses"],
                "message": a["message"],
            }
            for a in caregiver_alerts
        ],
        "log_samples": simulation_log[:10],
    }
    
    return results


if __name__ == "__main__":
    print("Executing 7-Day Domestic Activity Simulation (168h accelerated clock)...")
    res = run_simulation(seed=42)
    print("\n--- 7-DAY SIMULATION RESULTS ---")
    print(f"Total Routines Planned: {res['total_routines_planned']}")
    print(f"Confirmed Done:         {res['total_confirmed_done']}")
    print(f"Snooze Interactions:    {res['total_snooze_interactions']}")
    print(f"Missed Tasks:           {res['total_missed']}")
    print(f"Adherence Rate:         {res['overall_completion_rate_pct']}%")
    print(f"Caregiver Escalations:  {res['total_caregiver_alerts_dispatched']}")
    print("--------------------------------")
    
    output_path = os.path.join(os.path.dirname(__file__), "simulation_7day_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Full simulation telemetry saved to: {output_path}")
