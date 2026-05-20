class ServiceRequest {
  final String rawMessage;
  final String? serviceType;
  final String? locationName;
  final String? time;
  final String? urgency;

  ServiceRequest({
    required this.rawMessage,
    this.serviceType,
    this.locationName,
    this.time,
    this.urgency,
  });

  factory ServiceRequest.fromJson(Map<String, dynamic> json) {
    return ServiceRequest(
      rawMessage: json['raw_message'] ?? '',
      serviceType: json['intent_data']?['service_type'],
      locationName: json['intent_data']?['location_name'],
      time: json['intent_data']?['time'],
      urgency: json['intent_data']?['urgency'],
    );
  }
}

class ProviderModel {
  final String id;
  final String name;
  final double distanceKm;
  final double rating;
  final double score;
  final String reasoning;

  ProviderModel({
    required this.id,
    required this.name,
    required this.distanceKm,
    required this.rating,
    required this.score,
    required this.reasoning,
  });

  factory ProviderModel.fromJson(Map<String, dynamic> json) {
    return ProviderModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      distanceKm: (json['distance_km'] ?? 0).toDouble(),
      rating: (json['rating'] ?? 0).toDouble(),
      score: (json['score'] ?? 0).toDouble(),
      reasoning: json['reasoning'] ?? '',
    );
  }
}

class Booking {
  final String bookingId;
  final String status;
  final String message;
  final String? scheduledTime;
  final String? providerName;
  final bool remindersScheduled;
  final List<String> simulatedLogs;

  Booking({
    required this.bookingId,
    required this.status,
    required this.message,
    this.scheduledTime,
    this.providerName,
    this.remindersScheduled = false,
    this.simulatedLogs = const [],
  });

  factory Booking.fromJson(Map<String, dynamic> json) {
    List<String> logs = [];
    if (json['simulated_logs'] != null) {
      logs = List<String>.from(json['simulated_logs']);
    } else if (json['booking_details'] != null && json['booking_details']['simulated_logs'] != null) {
      logs = List<String>.from(json['booking_details']['simulated_logs']);
    }

    return Booking(
      bookingId: json['booking_id'] ?? json['booking_details']?['booking_id'] ?? '',
      status: json['status'] ?? json['booking_details']?['status'] ?? '',
      message: json['message'] ?? json['booking_details']?['message'] ?? '',
      scheduledTime: json['scheduled_time'],
      providerName: json['provider_name'],
      remindersScheduled: json['reminders_scheduled'] ?? json['booking_details']?['reminders_scheduled'] ?? false,
      simulatedLogs: logs,
    );
  }
}

class AgentLog {
  final String timestamp;
  final String agentName;
  final String toolUsed;
  final String decision;
  final String input;
  final String output;
  final String status; // success, error, cache, api

  AgentLog({
    required this.timestamp,
    required this.agentName,
    required this.toolUsed,
    required this.decision,
    required this.input,
    required this.output,
    required this.status,
  });

  factory AgentLog.fromJson(Map<String, dynamic> json) {
    String outputStr = '';
    if (json['output'] != null) {
      if (json['output'] is Map || json['output'] is List) {
        outputStr = json['output'].toString();
      } else {
        outputStr = json['output'].toString();
      }
    }

    // Attempt to infer status if not directly provided
    String s = json['status'] ?? 'success';
    String d = (json['decision'] ?? '').toLowerCase();
    if (d.contains('error') || d.contains('fail')) s = 'error';
    if (d.contains('cache')) s = 'cache';
    if (d.contains('api') || (json['tool_used'] ?? '').toLowerCase().contains('api')) s = 'api';

    return AgentLog(
      timestamp: json['timestamp'] ?? '',
      agentName: json['agent_name'] ?? json['agent'] ?? 'Unknown Agent',
      toolUsed: json['tool_used'] ?? json['action'] ?? '',
      decision: json['decision'] ?? json['reasoning'] ?? '',
      input: json['input']?.toString() ?? '',
      output: outputStr,
      status: s,
    );
  }
}
