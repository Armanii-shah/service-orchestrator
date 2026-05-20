import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'dart:convert';

class AgentLogsScreen extends StatefulWidget {
  @override
  _AgentLogsScreenState createState() => _AgentLogsScreenState();
}

class _AgentLogsScreenState extends State<AgentLogsScreen> {
  final HttpService _httpService = HttpService();
  List<AgentLog> _logs = [];
  List<AgentLog> _filteredLogs = [];
  bool _isLoading = true;
  String _currentFilter = 'All';

  final List<String> _filters = ['All', 'Success', 'Error', 'API', 'Cache'];

  @override
  void initState() {
    super.initState();
    _fetchLogs();
  }

  void _fetchLogs() async {
    setState(() => _isLoading = true);
    try {
      final logs = await _httpService.getAgentLogs();
      if (mounted) {
        setState(() {
          _logs = logs;
          _applyFilter(_currentFilter);
        });
      }
    } catch (e) {
      print("Error fetching logs: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _applyFilter(String filter) {
    setState(() {
      _currentFilter = filter;
      if (filter == 'All') {
        _filteredLogs = List.from(_logs);
      } else {
        _filteredLogs = _logs.where((l) => l.status.toLowerCase() == filter.toLowerCase()).toList();
      }
    });
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'success':
        return Colors.green[100]!;
      case 'error':
        return Colors.red[100]!;
      case 'cache':
        return Colors.blue[100]!;
      case 'api':
        return Colors.purple[100]!;
      default:
        return Colors.grey[200]!;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'success': return Icons.check_circle;
      case 'error': return Icons.error;
      case 'cache': return Icons.sd_storage;
      case 'api': return Icons.cloud;
      default: return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F5),
      appBar: AppBar(
        title: Text('Agent Execution Trace', style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFF075E54),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Colors.white),
            onPressed: _fetchLogs,
          )
        ],
      ),
      body: Column(
        children: [
          // Filter Row
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: _filters.map((filter) {
                bool isSelected = _currentFilter == filter;
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: FilterChip(
                    label: Text(filter, style: TextStyle(color: isSelected ? Colors.white : Colors.black87)),
                    selected: isSelected,
                    selectedColor: const Color(0xFF128C7E),
                    backgroundColor: Colors.white,
                    onSelected: (_) => _applyFilter(filter),
                  ),
                );
              }).toList(),
            ),
          ),
          
          Expanded(
            child: _isLoading
                ? Center(child: CircularProgressIndicator(color: const Color(0xFF075E54)))
                : _filteredLogs.isEmpty
                    ? Center(child: Text("No logs found for '$_currentFilter'"))
                    : ListView.builder(
                        padding: EdgeInsets.all(12),
                        itemCount: _filteredLogs.length,
                        itemBuilder: (context, index) {
                          final log = _filteredLogs[index];
                          return _buildLogCard(log);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildLogCard(AgentLog log) {
    Color bgColor = _getStatusColor(log.status);
    
    return Card(
      elevation: 2,
      margin: EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: bgColor.withOpacity(0.5), width: 2)
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          collapsedBackgroundColor: bgColor,
          backgroundColor: bgColor,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          collapsedShape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          title: Row(
            children: [
              Icon(_getStatusIcon(log.status), color: Colors.black54),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  log.agentName,
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
                ),
              ),
            ],
          ),
          subtitle: Text(
            '${log.timestamp} | Tool: ${log.toolUsed}',
            style: TextStyle(fontSize: 12, color: Colors.black54),
          ),
          children: [
            Container(
              padding: EdgeInsets.all(16),
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(bottomLeft: Radius.circular(12), bottomRight: Radius.circular(12)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildLogDetail('Decision / Reasoning:', log.decision),
                  SizedBox(height: 12),
                  _buildLogDetail('Input:', log.input),
                  SizedBox(height: 12),
                  _buildLogDetail('Output:', _formatJson(log.output)),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }

  String _formatJson(String val) {
    if (val.isEmpty) return 'N/A';
    try {
      final decoded = json.decode(val);
      return JsonEncoder.withIndent('  ').convert(decoded);
    } catch (e) {
      return val;
    }
  }

  Widget _buildLogDetail(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: const Color(0xFF075E54))),
        SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey[50],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Text(
            value.isEmpty ? 'N/A' : value,
            style: TextStyle(fontFamily: 'monospace', fontSize: 12, color: Colors.grey[800]),
          ),
        ),
      ],
    );
  }
}
