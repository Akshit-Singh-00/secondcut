# SecondCut demo script - target 3 minutes

This is a script for the final participant-recorded demo. The generated software walkthrough is a draft aid, not evidence of a physical build or cloud deployment.

## 0:00-0:15 - Team introduction

Akshit Singh appears or introduces himself. Say: "I'm Akshit Singh, and this is SecondCut, a camera-guided prototype that helps recover a cardboard project after a cutting mistake." The participant introduction still needs to be recorded; the title card alone is not a team video.

## 0:15-0:40 - Problem and scope

Show a real damaged blank if available. Explain that the first design is a two-panel organizer insert. It needs a second panel from separate stock and an existing container. The goal is to retain usable material while keeping both slots compatible.

## 0:40-1:25 - Working application

Open the verified deployment, or clearly identify the local build if cloud deployment remains pending. Run Missing corner. State explicitly that this built-in sample is generated. Show the measured outline, proposed dimensions, area retained for the main panel, and companion dimensions. Accept a repair and open the full-size SVG.

## 1:25-1:55 - Recovery loop

Upload a real cut panel if available. Otherwise use the synthetic repaired-panel example and label it. Show the geometry check and explain that physical fit is a separate hands-on validation. Show one replacement case and one recapture case.

## 1:55-2:25 - Architecture

Show docs/architecture.svg. OpenCV 5 performs marker calibration, perspective correction, and segmentation. A geometric solver and deterministic controller select next steps. If AWS deployment is verified, show the actual health endpoint and describe Lambda, S3, and CloudWatch. Otherwise say it is prepared infrastructure, not a deployed system.

## 2:25-2:50 - Evidence and limits

Show evaluation.json and the passing test run. Distinguish nine synthetic scenarios from any separately collected real photographs. Report only observed physical results, not target metrics. Mention the flat, contrasting cardboard assumption and manual thickness entry.

## 2:50-3:00 - Close

"SecondCut makes the next decision from the material that is actually left. Our next validation step is broader real-cardboard testing."

The final video must be publicly viewable or unlisted and hosted on a Devpost-supported platform. Do not place a placeholder or unrelated video URL in the submission.
