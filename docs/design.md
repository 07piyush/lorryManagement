# Comprehensive LR Processing System Design

## System Overview

The LR Processing System is a CLI-based application that ingests Excel sheets containing invoice data, generates unique LR IDs for each invoice, creates optimized PDFs with 3 LRs per page, stores data in a database, and manages the printing process. The system is designed to be modular, reliable, consistent, and scalable.

## 1. File Ingestion & Watcher

**Overview**: Monitors designated folders for new Excel files, handles file system events, and queues files for processing while preventing duplicate processing.

### Responsibilities & Interfaces
- **Inputs**: Path to watch directory, file pattern filters, debounce settings
- **Outputs**: Queue of ready-to-process Excel files
- **CLI Commands**: `watch`, `status`

### Key Design Decisions
- Use `watchdog` library for cross-platform file system monitoring
- Implement stateful watcher with local SQLite for restart/recovery
- Two-phase detection: size stabilization followed by content hash verification

### Reliability & Consistency Safeguards
- Handle file system permissions errors gracefully
- Use content hashing to prevent duplicate processing of renamed files
- Implement read-lock detection to avoid processing files still being written
- Maintain "seen files" registry with timestamps for deduplication

### Scalability & Extensibility Considerations
- Support for multiple watch directories with different processing rules
- Configurable polling vs. native event handling based on OS capability
- API to programmatically register new watch directories
- Extendable to support cloud storage sources via adapters

## 2. Sheet Reader & Preprocessor

**Overview**: Opens Excel files containing invoice data, extracts structured data from specified sheets, and transforms raw spreadsheet data into a clean, normalized list of invoice records.

### Responsibilities & Interfaces
- **Inputs**: Path to Excel file, sheet name, column mappings
- **Outputs**: List of dictionaries representing cleaned invoice rows
- **API**: Methods for reading/preprocessing Excel data

### Key Design Decisions
- Use `pandas` with `openpyxl` engine for Excel reading
- Apply column name normalization (case, spaces, special chars)
- Handle merged cells by propagating values
- Implement type coercion based on schema expectations
- Support header row detection or explicit column mapping

### Reliability & Consistency Safeguards
- Validate Excel file integrity before processing
- Handle malformed sheets with graceful degradation
- Report specific row/column errors without failing entire batch
- Implement maximum row limit protection against memory exhaustion
- Log preprocessing statistics (rows read, rows dropped, type conversions)

### Scalability & Extensibility Considerations
- Chunked reading for large files to manage memory
- Support multiple sheet processing in a single file
- Pluggable preprocessors for special data transformations
- Support for Excel formulas via configurable evaluation

## 3. Validation Engine

**Overview**: Applies business rules and validation constraints to invoice data before accepting it for processing, with support for configurable rule sets.

### Responsibilities & Interfaces
- **Inputs**: List of invoice record dictionaries, validation rule set
- **Outputs**: Validation results with pass/fail status and error details
- **API**: Methods for validating data against rules

### Key Design Decisions
- Schema-driven validation using `jsonschema` or `pydantic`
- Support for both generic and business-specific validation rules
- Custom validation functions for complex business rules
- Validation pipeline with early termination for critical errors

### Reliability & Consistency Safeguards
- Per-row validation with detailed error collection
- Support for "strict" and "lenient" validation modes
- Clearly defined "must-have" vs. "nice-to-have" fields
- Support for data coercion/fixing during validation
- Comprehensive error reporting with row numbers and values

### Scalability & Extensibility Considerations
- Pluggable validation rules via Python functions or YAML definition
- Versioned rule sets for backward compatibility
- Performance optimization for large datasets via parallel validation
- Support for custom data transformers during validation

## 4. LR ID Generator

**Overview**: Generates unique LR IDs for each valid invoice record based on configurable patterns and maintaining sequence integrity.

### Responsibilities & Interfaces
- **Inputs**: Validated invoice records, ID generation configuration
- **Outputs**: Same records enriched with generated LR IDs
- **API**: Methods for generating and managing LR IDs

### Key Design Decisions
- Use atomic counter in postgresql for sequence generation
- Support configurable ID patterns (prefix, date components, sequential number)
- Implement batch reservation of IDs to prevent duplicates
- Support different ID sequences for different branches/destinations

### Reliability & Consistency Safeguards
- Guarantee uniqueness through database transactions
- Handle rollbacks for failed batches
- Maintain counter integrity across system restarts
- Prevent gaps in sequence through careful reservation

### Scalability & Extensibility Considerations
- Support for distributed ID generation with conflict resolution
- Configurable sequence reset intervals (daily, monthly, yearly)
- Performance optimization for large batches
- API for checking ID availability and next ID prediction

## 5. Template Engine & PDF Generator

**Overview**: Generates optimized PDF documents containing 3 LR entries per page using configurable templates with dynamic layout.

### Responsibilities & Interfaces
- **Inputs**: List of records with generated LR IDs, template configuration
- **Outputs**: Generated PDF files (3 records per page)
- **API**: Methods for PDF generation and management

### Key Design Decisions
- Use `reportlab` for PDF generation
- Optimize layout for 3 LRs per A4 page
- YAML-based template definition with relative positioning
- Support for dynamic content sizing and overflow handling
- Built-in barcode and QR code generation

### Reliability & Consistency Safeguards
- Template validation before processing
- Content overflow detection and warning system
- Support for page breaks if an LR doesn't fit
- Font embedding for consistent rendering across systems
- Page boundary and margin enforcement

### Scalability & Extensibility Considerations
- Template versioning and backward compatibility
- Support for different items-per-page configurations
- Image asset management with caching
- Performance optimization for batch processing
- Support for custom rendering plugins

## 6. Database Layer

**Overview**: Manages persistent storage of processed invoice and LR records in a Database with transactional guarantees. Never stores PDFs, only data.

### Responsibilities & Interfaces
- **Inputs**: List of validated records with generated LR IDs
- **Outputs**: Success/failure status
- **API**: Methods for data storage and retrieval

### Key Design Decisions
- Use postgresql.
- Design efficient schema optimized for query patterns
- Store only data, never binary content like PDFs
- Implement transactional batch writes for atomicity
- Use compound keys for efficient retrieval

### Reliability & Consistency Safeguards
- Implement two-phase commit for batch processing
- Generate unique idempotency keys for each batch
- Validate postgres connection before starting batch
- Implement retry mechanism with exponential backoff
- Record batch metadata (timestamp, source file, status)

### Scalability & Extensibility Considerations
- Sharded data structure for high-volume scaling
- Efficient indexing for common query patterns
- Support for offline operation with sync on reconnect
- Data archiving strategy for historical records
- Performance monitoring for database operations

## 7. Print Dispatcher

**Overview**: Manages the delivery of generated PDFs to print devices, with support for queuing, retries, and print status tracking.

### Responsibilities & Interfaces
- **Inputs**: Generated PDF files, printer configuration
- **Outputs**: Print job status
- **CLI Commands**: Print control and status commands

### Key Design Decisions
- Support both direct printing and outbox folder approach
- Use CUPS or Windows printing subsystem via appropriate libraries
- Implement print queue management with prioritization
- Track print status via job IDs
- Support multiple printer targets

### Reliability & Consistency Safeguards
- Verify printer availability before queuing jobs
- Implement printer-specific error handling
- Create print job audit trail with statuses
- Support manual approval workflow option
- Handle print failures with retry logic

### Scalability & Extensibility Considerations
- Support for distributed print servers
- Load balancing across multiple printers
- Batch printing optimization
- Support for print profiles (quality, paper type)
- API for remote print job submission

## 8. Orchestration & CLI Controller

**Overview**: Coordinates the entire workflow from file detection to printing, provides user interface, and manages the overall system lifecycle.

### Responsibilities & Interfaces
- **Inputs**: User commands, configuration, system events
- **Outputs**: Process status, completion notifications
- **CLI Commands**: System management commands

### Key Design Decisions
- Use `click` or `typer` for CLI interface
- Implement command pattern for workflow steps
- Support both interactive and daemon modes
- Create workflow pipeline with observable state
- Implement graceful shutdown and pause/resume

### Reliability & Consistency Safeguards
- Handle system signals (SIGTERM, SIGINT)
- Implement graceful cancellation of in-progress operations
- Save workflow state for recovery
- Provide detailed progress reporting
- Support timeout and deadlock detection

### Scalability & Extensibility Considerations
- Support for parallel workflows
- Pluggable pipeline steps
- Configuration hot-reload capability
- Support for web API as alternative interface
- Event-driven architecture for extensibility

## 9. Error Handling & Logging

**Overview**: Provides comprehensive error management, logging, and telemetry across the system for troubleshooting and auditing.

### Responsibilities & Interfaces
- **Inputs**: System events, errors, metrics
- **Outputs**: Log files, alerts, audit records
- **API**: Logging and metrics collection methods

### Key Design Decisions
- Use structured logging with `structlog`
- Implement hierarchical error classification
- Create local audit database using SQLite
- Support both console and file logging
- Define standard error response format

### Reliability & Consistency Safeguards
- Ensure logs persist even during catastrophic failures
- Implement log rotation and archiving
- Create error aggregation to prevent alert storms
- Support different verbosity levels
- Implement sensitive data masking in logs

### Scalability & Extensibility Considerations
- Support for centralized logging systems
- Performance metrics collection
- Custom alerting integrations
- Log search and analysis capabilities
- User activity auditing

## 10. Configuration & Extensibility

**Overview**: Manages system configuration, provides extension points, and enables runtime customization without code changes.

### Responsibilities & Interfaces
- **Inputs**: Configuration files, environment variables
- **Outputs**: Validated configuration objects
- **API**: Configuration management methods

### Key Design Decisions
- Use YAML for configuration files with schema validation
- Support environment variable overrides
- Implement hierarchical configuration with inheritance
- Create plugin system for extensibility
- Support config hot-reload

### Reliability & Consistency Safeguards
- Validate configuration against schema before applying
- Support fallback configurations
- Version control configuration changes
- Implement configuration change audit log
- Prevent breaking changes during hot-reload

### Scalability & Extensibility Considerations
- Support for remote configuration storage
- Multi-tenant configuration isolation
- Feature flag system
- A/B testing framework
- Custom plugin development API

## Updated System Flow

1. **File Watcher** detects a new Excel file in the input directory
2. **Orchestrator** initiates processing pipeline  
3. **Sheet Reader** loads and normalizes the Excel invoice data
4. **Validation Engine** verifies all invoice records meet requirements
5. **LR ID Generator** creates unique LR IDs for each valid invoice
6. **Database Layer** stages the invoice and LR data in postgresql (transaction begins)
7. **PDF Generator** creates optimal A4 PDFs with 3 LRs per page
8. **Database Layer** commits the transaction with generated LR IDs
9. **Print Dispatcher** sends PDFs to configured printer
10. **Orchestrator** archives processed file and logs completion

# User Journeys

## Journey 1: Standard Success Flow

**User: Logistics Supervisor**
1. **Setup Phase**
   - User installs the LR Generator system on their office computer
   - User configures input folders, postgresql credentials, and printer settings
   - User configures LR ID pattern as "LR-${YYYYMMDD}-${SEQ:6}"
   - User runs the system in daemon mode to monitor input folder

2. **Processing Phase**
   - User receives an Excel file with 45 invoice entries via email
   - User saves the Excel file to the configured input folder
   - System detects the new file and begins processing
   - System displays: "Processing file: invoices_042825.xlsx (45 entries)"
   - System validates all invoice entries successfully
   - System generates 45 unique LR IDs in sequence LR-20250428-000001 through LR-20250428-000045
   - System stores all data in postgresql (no PDFs stored)
   - System generates 15 PDFs (3 LRs per page)
   - System sends PDFs to printer and displays: "All 45 LRs processed and sent to printer (15 pages)"

3. **Completion Phase**
   - User receives 15 printed pages, each containing 3 LR slips
   - System archives the original Excel file to the processed directory
   - System logs completion in the audit trail
   - User can query postgresql to view all processed LR records

## Journey 2: Validation Error Flow

**User: Data Entry Operator**
1. **Preparation Phase**
   - User prepares an Excel sheet with new invoice entries
   - User accidentally enters negative weights for some items
   - User saves the file to the monitored input folder

2. **Error Detection Phase**
   - System detects file and begins processing
   - System reads all entries and begins validation
   - System encounters validation errors on rows with negative weights
   - System halts processing and shows detailed error report:
     * Row 7: "Weight KG must be positive. Found: -12.5"
     * Row 18: "Weight KG must be positive. Found: -8.3"

3. **Correction Phase**
   - User opens the original Excel file and corrects the weight values
   - User saves the corrected file back to the input folder
   - System processes the corrected file successfully
   - System moves the file to processed directory after completion

## Journey 3: LR ID Generation Sequence Recovery

**User: IT Support Technician**
1. **Normal Operation Phase**
   - System has been running and processing files
   - System has already generated LRs up to LR-20250428-000120

2. **System Crash Phase**
   - System crashes unexpectedly during processing
   - When restarted, system needs to determine next available LR number

3. **Recovery Phase**
   - System queries postgresql for the highest LR ID in the current sequence
   - System finds LR-20250428-000120 as the highest value
   - System resumes sequence from LR-20250428-000121
   - System logs: "LR sequence recovered. Continuing from LR-20250428-000121"
   - Processing continues with correct sequence integrity

## Journey 4: Template Modification for PDF Layout

**User: Process Manager**
1. **Requirement Change Phase**
   - User needs to update the LR template to add a new field for GST number
   - User also wants to change layout to improve readability

2. **Configuration Update Phase**
   - User modifies the template configuration to include the GST number field
   - User adjusts positioning of elements to prevent overlap
   - User updates the template version number to track changes

3. **Testing Phase**
   - User runs system with test file to verify new template
   - System generates PDFs with updated layout
   - User approves the changes and deploys to production
   - All subsequent batches use the new template format

## Journey 5: High Volume Processing

**User: Operations Team During Peak Season**
1. **Preparation Phase**
   - Team expects high volume processing day with 1000+ invoices
   - Team adjusts configuration to optimize for performance:
     * Increases batch size for ID generation
     * Enables parallel processing for PDF generation

2. **Processing Phase**
   - Team uploads multiple large Excel files to input folder
   - System detects high workload and manages resources accordingly
   - System processes invoices in optimal batches
   - System shows real-time progress: "Processed 450/1200 invoices (38%)"

3. **Monitoring Phase**
   - Team monitors system performance via status commands
   - System manages memory efficiently by streaming PDFs directly to print
   - System completes all processing within expected timeframe
   - Team receives all printed LRs organized by batch

## Journey 6: Network Disruption

**User: Branch Office Manager**
1. **Initial Processing Phase**
   - User places Excel file in input folder for processing
   - System validates all data successfully
   - System generates LR IDs for all invoices

2. **Network Disruption Phase**
   - Internet connection goes down during postgresql upload
   - System detects connection failure
   - System queues transactions for retry and continues PDF generation
   - System shows: "Network connection lost. Data will sync when connection restored."

3. **Resolution Phase**
   - After several minutes, network connection is restored
   - System automatically detects connectivity and syncs pending data
   - System uses idempotency keys to prevent duplicate entries
   - System completes processing and printing despite the interruption

## Journey 7: Configuration Changes

**User: System Administrator**
1. **Performance Tuning Phase**
   - Administrator notices PDF generation is a bottleneck
   - Administrator modifies configuration to optimize this process
   - Administrator adjusts concurrent generation parameters

2. **Hot Reload Phase**
   - Administrator runs configuration reload command
   - System validates new configuration
   - System applies changes without requiring restart
   - System logs: "Configuration updated successfully"

3. **Verification Phase**
   - Administrator monitors system performance with new settings
   - System processes subsequent files with improved performance
   - Administrator commits configuration changes to version control

## Journey 8: Multi-Template Support

**User: Regional Manager with Multiple Branches**
1. **Setup Phase**
   - Manager needs different LR formats for different regions
   - Manager configures branch-specific templates
   - Manager sets up branch-specific LR ID patterns:
     * "DEL-${YYYYMMDD}-${SEQ:4}" for Delhi
     * "MUM-${YYYYMMDD}-${SEQ:4}" for Mumbai

2. **Processing Phase**
   - System detects branch code in Excel files
   - System selects appropriate template and ID pattern based on branch
   - System generates branch-specific LRs and PDFs
   - System maintains separate ID sequences for each branch

3. **Review Phase**
   - Manager reviews printed LRs from different branches
   - Each branch has consistent formatting and sequencing
   - Manager can query postgresql to get branch-specific reports

## Journey 9: Audit and Compliance

**User: Compliance Officer**
1. **Audit Preparation Phase**
   - Officer needs complete processing history for last month
   - Officer runs audit report command with date range filter
   - System generates comprehensive audit log showing all operations

2. **Validation Phase**
   - Officer verifies all invoices have corresponding LRs
   - Officer checks for sequence gaps or anomalies
   - System provides detailed transaction history from postgresql
   - Officer verifies template versions used for compliance

3. **Report Generation Phase**
   - Officer requests system statistics and metrics
   - System generates performance and throughput reports
   - Officer uses data to certify compliance with company policies

## Journey 10: System Extension

**User: Developer**
1. **Requirements Phase**
   - Developer needs to add real-time dashboard for monitoring
   - Developer studies extension points in the application

2. **Development Phase**
   - Developer creates plugin that exposes metrics via REST API
   - Developer integrates with existing logging and metrics
   - Developer updates configuration to enable the plugin

3. **Deployment Phase**
   - Developer deploys update without disrupting ongoing operations
   - System continues processing while exposing new API endpoints
   - Operations team connects dashboard to new metrics API
   - Real-time monitoring now available alongside existing functionality

These user journeys illustrate how the revised system handles various scenarios from normal operations to error conditions, recovery processes, and extensions. The modular design ensures data consistency while accommodating business needs like generating unique LR IDs for invoices and optimizing PDF layout for 3 LRs per page.