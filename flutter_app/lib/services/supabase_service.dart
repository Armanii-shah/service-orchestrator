import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter/material.dart';

import 'api_service.dart';

class SupabaseService {
  static final SupabaseService _instance = SupabaseService._internal();
  factory SupabaseService() => _instance;
  SupabaseService._internal();

  SupabaseClient get client => Supabase.instance.client;

  void setupAuthListener() {
    client.auth.onAuthStateChange.listen((data) {
      final AuthChangeEvent event = data.event;
      if (event == AuthChangeEvent.signedOut) {
        if (HttpService.navigatorKey.currentState != null) {
          HttpService.navigatorKey.currentState!.pushNamedAndRemoveUntil('/login', (route) => false);
        }
      }
    });
  }
}
