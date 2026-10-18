# ResQ AI: Datathon Demo Script

## 1. Demo Objective

Demonstrate how ResQ AI organizes synthetic incident reports, provides transparent priority assessments, identifies geographic concentrations, and recommends potentially suitable response resources for coordinator review.

**Important:** This is a prototype demonstration using synthetic data. It does not dispatch real emergency services.

## 2. Suggested Demo Sequence

### Step 1: Introduce the Problem

Explain that disaster-response coordination can involve incident reports, severity assessments, geographic patterns, and limited response resources. When information is fragmented, coordinators may find it difficult to review incidents and compare available resources efficiently.

### Step 2: Introduce ResQ AI

ResQ AI is a disaster-response intelligence and decision-support prototype. Its core workflow can be applied broadly, with India as an initial focus.

The prototype brings together:
- Incident management and transparent priority scoring.
- Geographic hotspot detection.
- Capability-aware resource recommendations.
- Resource assignment and release tracking.
- A dashboard for reviewing incident and resource information.

### Step 3: Show the Overview Dashboard

Open the Streamlit application and present the Overview section.

Explain that the displayed records are synthetic demonstration data. Point out the available incident and resource summaries, and clarify that the figures illustrate the workflow rather than report real emergencies.

### Step 4: Review an Incident

Open Incident Management and select an incident.

Explain how the prototype uses structured incident information, including severity and the number of people affected, to calculate a deterministic priority score.

Highlight that verification status does not increase or decrease the score. Unverified or pending reports receive additional review flags, and every priority assessment requires human review.

Do not describe this score as a clinically or operationally validated triage model.

### Step 5: Demonstrate Hotspot Detection

Open Hotspot Detection.

Explain that the prototype uses DBSCAN clustering with geographic coordinates to identify concentrations of incident reports within a configurable distance.

Show the cluster results and map, where available. Explain that a hotspot indicates a spatial concentration in the supplied data. It is not a forecast of where the next disaster will occur.

### Step 6: Demonstrate Resource Recommendations

Open Resource Allocation and choose an eligible incident.

Generate recommendations and explain that the matching logic considers:
- Resource capability.
- Availability.
- Capacity.
- Geographic distance.
- A configurable maximum distance.

Clarify that the displayed distance is straight-line distance, not road distance or a live travel-time estimate. Recommendations are suggestions for coordinator review, not automatic dispatch decisions.

### Step 7: Assign a Resource

Choose an appropriate recommended resource and use the dashboard's assignment workflow.

Explain that the database records the assignment and that an active assignment prevents the same resource from being assigned to another incident simultaneously.

Generate recommendations again and show that an actively assigned resource is no longer treated as available for a new assignment.

### Step 8: Release the Resource

Release the assignment using the dashboard.

Generate recommendations again and show that the released resource can become eligible for matching, provided its other eligibility conditions are satisfied.

Explain that assignment and release actions are recorded in the audit log.

### Step 9: Explore the Data

Open Data Explorer and show the available incident or resource records.

Reinforce that the underlying demonstration dataset is synthetic and that locations are approximate. Do not present generated records as verified real-world incident reports.

### Step 10: Close with the Value Proposition

Summarize the demonstrated workflow:

**Incident data → transparent priority assessment → hotspot analysis → resource recommendations → coordinator-reviewed assignment → auditable release.**

ResQ AI demonstrates how these capabilities can be combined in one interface while keeping decisions explainable and under human control.

## 3. Suggested Closing Statement

"ResQ AI is a prototype for disaster-response decision support. It combines explainable priority scoring, geographic clustering, capability-aware resource matching, and assignment tracking in a single workflow. Our current demonstration uses synthetic data and does not connect to live emergency systems. The next stage would focus on data-source validation, stronger operational testing, security, reliability, and carefully governed integration with real response workflows."

## 4. Questions to Be Ready For

**Is the data real?**  
No. The current demonstration uses synthetic incident and resource records.

**Does the system automatically dispatch emergency services?**  
No. It recommends resources and records coordinator-managed assignments.

**Does hotspot detection predict future disasters?**  
No. It identifies geographic concentrations in the supplied incident data.

**Does the system calculate actual arrival times?**  
No. Resource matching uses straight-line geographic distance, not road-network routing or live traffic.

**How is priority calculated?**  
A deterministic rule-based score uses incident severity and the reported number of people affected. Verification status adds review flags rather than changing the score.

**Can every recommendation be trusted automatically?**  
No. Recommendations may be incomplete or unsuitable when data is missing, stale, inaccurate, or insufficient. A coordinator must review them.

**Is this deployed on IBM Z?**  
Do not claim an IBM Z deployment unless one has actually been implemented and verified. Describe any future IBM Z integration as proposed work.

**What would be required for real-world use?**  
Validated data sources, operational and safety evaluation, security and access controls, resilience testing, integration with authorized response organizations, and documented human-oversight procedures.

## 5. Demo Checklist

- [ ] Confirm the virtual environment is active.
- [ ] Confirm the application launches.
- [ ] Confirm the dashboard displays its synthetic-data warning.
- [ ] Demonstrate incident priority assessment.
- [ ] Demonstrate hotspot clustering.
- [ ] Generate resource recommendations.
- [ ] Assign a resource and show it is excluded from subsequent recommendations.
- [ ] Release the assignment and demonstrate eligibility again.
- [ ] Show the data explorer and explain the synthetic dataset.
- [ ] Avoid claiming live feeds, real dispatch, validated triage, road ETAs, or an unimplemented IBM Z deployment.
