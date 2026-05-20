import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/models.dart';
import 'supabase_service.dart'; 

class HttpService {
  static const String baseUrl = 'http://127.0.0.1:8000';
  
  static final HttpService _instance = HttpService._internal();
  factory HttpService() => _instance;
  HttpService._internal();

  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  Future<Map<String, String>> _getHeaders() async {
    final session = Supabase.instance.client.auth.currentSession;
    final token = session?.accessToken;
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  void _forceLogout() async {
    await Supabase.instance.client.auth.signOut();
  }

  Future<dynamic> _fetchWithRetry(String endpoint, Future<http.Response> Function() request, {int retries = 3}) async {
    for (int i = 0; i < retries; i++) {
      try {
        final response = await request().timeout(const Duration(seconds: 10));
        
        if (response.statusCode >= 200 && response.statusCode < 300) {
          return json.decode(response.body);
        } else {
          if (response.statusCode == 401) {
            _forceLogout();
            throw Exception('Session Expired. Please login again.');
          }
          final body = json.decode(response.body);
          final errorMsg = body['detail'] ?? 'Server error';
          if (i == retries - 1) throw Exception(errorMsg);
        }
      } catch (e) {
        if (i == retries - 1) {
          if (e is TimeoutException) throw Exception('Server busy, retry?');
          throw Exception(e.toString().replaceAll("Exception: ", ""));
        }
        await Future.delayed(const Duration(seconds: 2));
      }
    }
  }

  // --- Auth Backend Endpoints ---
  Future<Map<String, dynamic>> register(String email, String password, String fullName, String phone) async {
    final String url = baseUrl + '/auth/register';
    final response = await _fetchWithRetry(url, () => http.post(
      Uri.parse(url), 
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email, 'password': password, 'full_name': fullName, 'phone': phone})
    ), retries: 1); 
    return response;
  }

  Future<Map<String, dynamic>> resendConfirmation(String email) async {
    final String url = baseUrl + '/auth/resend-confirmation';
    final response = await _fetchWithRetry(url, () => http.post(
      Uri.parse(url), 
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email})
    ), retries: 1);
    return response;
  }
  
  Future<Map<String, dynamic>> getMe() async {
    final String url = baseUrl + '/auth/me';
    final headers = await _getHeaders();
    return await _fetchWithRetry(url, () => http.get(Uri.parse(url), headers: headers));
  }

  Future<Map<String, dynamic>> updateCity(String city) async {
    final String url = baseUrl + '/api/update-city';
    final headers = await _getHeaders();
    final response = await _fetchWithRetry(url, () => http.post(
      Uri.parse(url),
      headers: headers,
      body: json.encode({'city': city})
    ), retries: 1);
    return response;
  }

  // --- App Endpoints ---
  Future<Map<String, dynamic>> processRequest(String message, {String? providerId, String? serviceType, String? location}) async {
    final String url = baseUrl + '/api/process-request';
    final headers = await _getHeaders();
    final Map<String, dynamic> body = {'message': message, 'language': 'Roman Urdu'};
    if (providerId != null) body['selected_provider_id'] = providerId;
    if (serviceType != null) body['service_type'] = serviceType;
    if (location != null) body['location'] = location;
    
    final response = await _fetchWithRetry(url, () => http.post(
      Uri.parse(url),
      headers: headers,
      body: json.encode(body),
    ));
    return response;
  }

  Future<List<ProviderModel>> getProviders(String serviceType) async {
    final String url = baseUrl + '/api/providers/' + serviceType;
    final headers = await _getHeaders();
    final response = await _fetchWithRetry(url, () => http.get(Uri.parse(url), headers: headers));
    if (response != null && response is List) {
      return response.map((p) => ProviderModel.fromJson(p)).toList();
    }
    return [];
  }

  Future<Booking> bookProvider(String providerId, Map<String, dynamic> contextData) async {
    final String url = baseUrl + '/api/booking/' + providerId;
    final headers = await _getHeaders();
    final response = await _fetchWithRetry(url, () => http.get(Uri.parse(url), headers: headers));
    return Booking.fromJson(response);
  }

  Future<List<AgentLog>> getAgentLogs() async {
    final String url = baseUrl + '/api/agent-logs';
    final headers = await _getHeaders();
    try {
      final response = await _fetchWithRetry(url, () => http.get(Uri.parse(url), headers: headers));
      if (response != null && response is List) {
        return response.map((l) => AgentLog.fromJson(l)).toList();
      } else if (response != null && response['logs'] != null) {
        return (response['logs'] as List).map((l) => AgentLog.fromJson(l)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }
}
