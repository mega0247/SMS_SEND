# SMS License Manager

This repository contains Python scripts to **generate** and **validate** license files for SMS sending software.  
The licenses include encrypted user details and validity dates to control software access.

---

## Files

- `generate_license.py`  
  Creates encrypted license files (`license_<user_id>.key`) and an initial encrypted daily log (`daily_log.enc`).  
  Usage: run the script to generate license and daily log files for a user.

- `validate_license.py`  
  Validates a given license file against an expected user ID and checks if the license is active and not expired.  
  Usage:  
  ```bash
  python validate_license.py <license_file> <expected_user_id>
