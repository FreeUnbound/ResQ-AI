# ResQ AI: Limitations, Risks, and Future Improvements

## 1. Current Prototype Scope

ResQ AI is a disaster-response decision-support prototype. It demonstrates incident management, deterministic priority scoring, geographic hotspot clustering, resource recommendations, and coordinator-managed resource assignments.

The current implementation is intended for demonstration and evaluation. It is not a production emergency-response system.

## 2. Data Limitations

### Synthetic Demonstration Data

The current incident and resource records are generated for demonstration purposes. They do not represent verified real-world emergencies or actual operational resource inventories.

**Risk:** Demonstrations may appear more reliable than real operations if synthetic records are mistaken for live data.

**Future improvement:** Integrate authorized data sources after assessing data quality, access permissions, update frequency, provenance, and validation requirements. Clearly distinguish real, simulated, stale, and unverified records.

### Approximate Geographic Locations

The demonstration dataset uses approximate locations.

**Risk:** Geographic recommendations and clusters may not represent actual incident locations or accessible routes.

**Future improvement:** Validate geospatial data and use suitable mapping and routing services where authorized and available.

## 3. Priority Scoring Limitations

The priority score uses deterministic rules based on incident severity and the reported number of people affected. Verification status creates review flags but does not change the score.

**Risks:**
- Incorrect, missing, or exaggerated incident details can affect the score.
- The rules have not been established as a validated emergency triage method.
- A numerical score cannot capture every operational circumstance.
- Equal scores do not necessarily imply equal real-world urgency.

**Future improvement:** Work with qualified emergency-response stakeholders to define and evaluate operational criteria, document intended use, assess edge cases, and retain human oversight. Any proposed changes should be tested before operational use.

## 4. Hotspot Detection Limitations

The prototype uses DBSCAN clustering to identify spatial concentrations in the supplied incident records.

**Risks:**
- Results depend on the selected distance radius, minimum sample count, location quality, and distribution of reports.
- Sparse reporting can hide a genuine concentration.
- Duplicate or inaccurate reports can create misleading patterns.
- A detected cluster does not establish causation or predict a future disaster.

**Future improvement:** Add data-quality checks, timestamp-aware analysis, sensitivity testing, and clearly communicated uncertainty. Evaluate the method using appropriate historical or simulated scenarios before drawing operational conclusions.

## 5. Resource Matching Limitations

The matching module considers resource capability, availability, capacity, straight-line geographic distance, and a configurable maximum distance.

**Risks:**
- Straight-line distance is not road distance or estimated travel time.
- Resource records may be outdated or incomplete.
- Capability labels and capacity values may not fully represent real operational suitability.
- The closest matching resource may not be the safest or most appropriate choice in a complex situation.

**Future improvement:** Add verified, time-stamped resource status; validated capability and capacity definitions; road-network routing where available; access constraints; and appropriate coordinator review.

## 6. Assignment and Database Limitations

The prototype stores incident, resource, assignment, and audit information in a local SQLite database.

**Risks:**
- The current local deployment is not a complete multi-agency production platform.
- It does not establish that all external resource systems remain synchronized.
- Audit records do not independently prove that an action was operationally correct.
- Recovery, backup, access governance, and multi-user operational resilience require further evaluation.

**Future improvement:** Test backup and recovery, concurrent access, authentication, authorization, retention policies, audit integrity, and integration boundaries before production deployment.

## 7. Security and Privacy

The current demonstration does not establish production-grade security or privacy compliance.

**Risks:**
- Real incident reports could contain sensitive personal or location information.
- Unauthorized access or inappropriate disclosure could create harm.
- Data-sharing rules may differ across organizations and jurisdictions.

**Future improvement:** Define a security model, minimize collected personal data, enforce least-privilege access, protect data in transit and at rest, establish retention policies, and complete relevant security and privacy reviews before handling real operational data.

## 8. Reliability and Integration

The prototype does not currently connect to live emergency feeds, verified dispatch systems, or real-time traffic services.

It should not be represented as a live dispatch platform or as a deployed IBM Z solution unless those integrations are implemented and verified.

**Future improvement:** Define integration contracts, monitor data freshness and service health, handle partial failures, test degraded modes, and evaluate any proposed IBM Z deployment against concrete requirements.

## 9. Human Oversight

ResQ AI presents information and recommendations for coordinator review. It does not replace emergency-response professionals or make autonomous dispatch decisions.

Before any real-world use, authorized personnel must be able to inspect supporting information, understand uncertainty, reject recommendations, and follow established emergency procedures.

## 10. Development Roadmap

1. **Data validation:** Establish provenance, timestamps, freshness indicators, duplicate handling, and validation rules.
2. **Evaluation:** Create documented test scenarios for priority scoring, hotspot detection, and resource matching.
3. **Geospatial capability:** Evaluate routing and access constraints using approved sources.
4. **Operational resilience:** Test backup, recovery, concurrency, error handling, and degraded operation.
5. **Security and governance:** Define access controls, audit requirements, privacy safeguards, and retention policies.
6. **Integration:** Assess authorized data and response-system integrations.
7. **Deployment evaluation:** Investigate an IBM Z deployment only after requirements, architecture, and implementation have been established.

## 11. Responsible Use Statement

ResQ AI is currently a demonstration prototype using synthetic data and approximate locations. Its scores, clusters, and recommendations are not validated for real-world emergency operations. All outputs require human interpretation and review. Real-world use would require appropriate data validation, stakeholder evaluation, security controls, operational testing, and authorized integration.
