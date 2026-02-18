# IRIS System Documentation

## 1. Introduction
IRIS (Innovation Platform) is a comprehensive system designed to foster innovation within the organization. It allows employees to submit ideas, participate in challenges, and collaborate on solutions. The system supports multiple roles, each with specific workflows and permissions.

## 2. Role-Wise Process Flows

### 2.1 Employee (Ideator)
**Objective:** Submit ideas, join challenges, and track progress.
1.  **Login:** Users log in using their credentials.
2.  **Dashboard:**
    *   View "My Dashboard" for a personalized summary of points, ideas, and active challenges.
    *   View "Grassroot Dashboard" for status of process improvement ideas.
3.  **Submit Idea:**
    *   **Challenge Idea:** Navigate to a specific Challenge -> Click "Submit Idea" -> Complete the 4-step wizard (Basics, Solution, Collab, Review).
    *   **Grassroot Idea:** Click "Submit Grassroot Idea" (or via Dashboard) -> Complete the 4-step wizard.
4.  **Track Status:** View the status of submitted ideas in "My Ideas" or the respective dashboard.
5.  **Notifications:** Receive alerts for status changes, rewards, or comments.

### 2.2 Challenge Owner
**Objective:** Create and manage innovation challenges.
1.  **Create Challenge:**
    *   Navigate to "Post Challenge".
    *   Define Challenge details (Title, Description, Dates, Criteria).
    *   Select Evaluation Panels and Mentors.
    *   Publish the Challenge.
2.  **Manage Challenge:**
    *   View "Challenge Dashboard" to track submissions.
    *   **Manage Panels:** Assign or modify evaluation panels.
    *   **Manage Mentors:** Add or remove mentors for the challenge.
3.  **Review & Shortlist:**
    *   Oversee the evaluation process.
    *   Shortlist ideas for subsequent rounds.

### 2.3 Mentor
**Objective:** Guide ideators and refine ideas.
1.  **Dashboard:** View assigned challenges and ideas requiring mentorship.
2.  **Mentoring:**
    *   Access ideas assigned for mentorship.
    *   Provide feedback and suggestions via the comments section.
    *   Help ideators refine their "Solution" and "Value Proposition".

### 2.4 Evaluator (Panel Member)
**Objective:** Evaluate submitted ideas against defined criteria.
1.  **Evaluation Dashboard:** View ideas assigned for review.
2.  **Evaluate:**
    *   Open an idea.
    *   Rate the idea based on parameters (e.g., Feasibility, Impact, Innovation).
    *   Submit the evaluation.

### 2.5 IBU Head / Approver
**Objective:** Approve Grassroot ideas and high-level challenge outcomes.
1.  **Approver Dashboard:** View ideas pending approval (Grassroot ideas primarily).
2.  **Action:**
    *   **Approve:** Validate the idea and business value.
    *   **Reject:** Provide reasons for rejection.
    *   **Rework:** Send back to the ideator for more details.

### 2.6 Admin (Superuser)
**Objective:** System maintenance and master data management.
1.  **Admin Panel:** Access the Django Admin interface (`/admin`).
2.  **User Management:** Manage `IrisUser`, roles, and permissions.
3.  **Master Data:** Manage `IrisEmployeeMaster`, `ImprovementCategory`, `Department`, etc.
4.  **System Config:** Configure rewards, badges, and system-wide settings.

---

## 3. Database Schema
The system captures data across several key tables. Below is an overview of the primary tables and their purpose.

### Core User & Role Management
*   **`iris_users`**: Stores user credentials, profile info, and authentication details.
    *   *Key Fields*: `user_id` (PK), `email`, `full_name`, `user_type`, `employee_master` (FK).
*   **`iris_roles`**: Defines the available system roles (Challenge Owner, Mentor, etc.).
    *   *Key Fields*: `role_id` (PK), `role_name`.
*   **`iris_user_roles`**: Maps users to specific roles.
    *   *Key Fields*: `user` (FK), `role` (FK).
*   **`iris_employee_master`**: Master data for all employees (synced from HR system).
    *   *Key Fields*: `empcode` (PK), `empname`, `emailid`, `grade`, `supervisor`.

### Challenge Management
*   **`iris_challenges`**: Stores details of innovation challenges.
    *   *Key Fields*: `challenge_id` (PK), `title`, `status` (DRAFT, LIVE, COMPLETED), `start_date`, `end_date`, `challenge_owner` (FK).
*   **`iris_challenge_panels`**: Evaluation panels assigned to a challenge.
*   **`iris_challenge_mentors`**: Mentors assigned to a challenge.

### Idea Management
*   **`iris_ideas`**: Main table for idea submissions (linked to Challenges).
    *   *Key Fields*: `idea_id` (PK), `title`, `description`, `submitter` (FK), `challenge` (FK), `status`.
*   **`iris_idea_details`**: Extended details for an idea (Solution, Business Value).
    *   *Key Fields*: `idea` (FK), `proposed_solution`, `business_value`.
*   **`iris_grassroot_ideas`**: Specific table for Grassroot (Process Improvement) ideas.
    *   *Key Fields*: `grassroot_id` (PK), `proposed_idea`, `improvement_category` (FK), `status`.

### Evaluation & collaboration
*   **`iris_reviews`**: Stores evaluations and ratings for ideas.
    *   *Key Fields*: `review_id` (PK), `entity_id` (Idea ID), `reviewer` (FK), `rating`, `comments`.
*   **`iris_co_ideators`**: Collaborators working on a specific idea.
*   **`iris_comments`**: Threaded comments/discussions on ideas.

### Rewards & Gamification
*   **`iris_rewards`**: Points earned by users.
    *   *Key Fields*: `reward_id` (PK), `user` (FK), `points`, `reason`.
*   **`iris_badges`**: Badges available in the system.
*   **`iris_user_badges`**: Badges earned by users.

### System & Logs
*   **`iris_notifications`**: System notifications for users.
*   **`iris_workflow_logs`**: Audit trail of status changes for ideas and challenges.
*   **`django_session`**: User session data.

---

## 4. Operational Notes
*   **Data Backup:** A full database dump can be generated using the `dumpdata` command.
*   **User Sync:** Employee master data should be periodically synced with the central HR repository.
*   **Role Setup:** New Challenge Owners must be explicitly assigned the role by an Admin.
