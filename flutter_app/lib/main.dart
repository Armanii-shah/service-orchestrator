import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/chat_screen.dart';
import 'services/supabase_service.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await Supabase.initialize(
    url: 'https://hohiqcsogfooatpjuthz.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhvaGlxY3NvZ2Zvb2F0cGp1dGh6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyNzI4ODMsImV4cCI6MjA5NDg0ODg4M30.6zF2mlQAcU7i3E2n4IQrWhBG5ExmuF6ohROwoa20KSU',
  );

  // Setup auth redirect listener
  SupabaseService().setupAuthListener();

  final session = Supabase.instance.client.auth.currentSession;
  
  runApp(MyApp(initialRoute: session != null ? '/chat' : '/login'));
}

class MyApp extends StatelessWidget {
  final String initialRoute;
  MyApp({required this.initialRoute});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Service Orchestrator',
      navigatorKey: HttpService.navigatorKey, 
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: const Color(0xFF075E54),
        scaffoldBackgroundColor: const Color(0xFFF0F2F5),
        colorScheme: ColorScheme.fromSwatch().copyWith(
          primary: const Color(0xFF075E54),
          secondary: const Color(0xFF128C7E),
        ),
        fontFamily: 'Roboto',
      ),
      initialRoute: initialRoute,
      routes: {
        '/login': (context) => LoginScreen(),
        '/register': (context) => RegisterScreen(),
        '/chat': (context) => ChatScreen(),
      },
    );
  }
}
