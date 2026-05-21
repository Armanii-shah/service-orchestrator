import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import 'provider_list_screen.dart';
import 'booking_screen.dart';
import 'agent_logs_screen.dart';
import 'profile_tab.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? contextData;
  final bool isError;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.contextData,
    this.isError = false,
  });
}

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  int _currentIndex = 0;
  String _welcomeName = "Loading...";
  String? _preferredCity;
  final HttpService _httpService = HttpService();

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  void _loadUser() async {
    try {
      final user = await _httpService.getMe();
      if (user.containsKey('full_name')) {
        setState(() {
          _welcomeName = user['full_name'] ?? user['phone'] ?? "User";
          _preferredCity = user['preferred_city'];
        });
      } else if (user.containsKey('user')) {
        setState(() {
          _welcomeName = user['user']['full_name'] ?? user['user']['phone'] ?? "User";
          _preferredCity = user['user']['preferred_city'];
        });
      }
    } catch (e) {
      setState(() => _welcomeName = "User");
    }
  }

  void _logout() async {
    await Supabase.instance.client.auth.signOut();
    // main.dart's auth listener handles the redirect to login
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> _screens = [
      ChatTab(welcomeName: _welcomeName),
      AgentLogsScreen(),
      ProfileTab(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Service Orchestrator', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20, letterSpacing: 0.5)),
            Text('Welcome, $_welcomeName', style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 13, fontWeight: FontWeight.w400)),
          ],
        ),
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
        elevation: 4,
        shadowColor: Colors.black45,
        actions: [
          IconButton(
            icon: Icon(Icons.logout, color: Colors.white),
            onPressed: _logout,
            tooltip: 'Logout',
          )
        ],
      ),
      body: Center(
        child: Container(
          constraints: BoxConstraints(maxWidth: 800),
          decoration: BoxDecoration(
            color: const Color(0xFFF4F7F6),
            boxShadow: [
              BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 20, spreadRadius: 5),
            ],
          ),
          child: _screens[_currentIndex],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: const Color(0xFF075E54),
        unselectedItemColor: Colors.grey,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.chat), label: 'Chat'),
          BottomNavigationBarItem(icon: Icon(Icons.memory), label: 'Agent Logs'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}

// ----------------------------------------------------------------------
// CHAT TAB LOGIC
// ----------------------------------------------------------------------

class ChatTab extends StatefulWidget {
  final String welcomeName;
  ChatTab({required this.welcomeName});

  @override
  _ChatTabState createState() => _ChatTabState();
}

class _ChatTabState extends State<ChatTab> with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  final HttpService _httpService = HttpService();
  late AnimationController _animController;
  
  String? _lastService;
  String? _lastCity;
  bool _awaitingArea = false;
  bool _awaitingCity = false;
  
  @override
  void initState() {
    super.initState();
    _animController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..repeat();
    _messages.add(ChatMessage(text: "Assalam o Alaikum! Service Orchestrator mein khush aamdeed. Aapko kis service ki zaroorat hai?", isUser: false));
  }

  @override
  void dispose() {
    _animController.dispose();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage({String? overrideText}) async {
    final textToSend = overrideText ?? _controller.text.trim();
    if (textToSend.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: textToSend, isUser: true));
      _controller.clear();
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await _httpService.processRequest(
        textToSend,
        serviceType: _awaitingArea ? _lastService : null,
        location: _awaitingArea ? _lastCity : null,
      );
      
      String agentReply = "I am processing your request...";
      bool isError = false;
      
      if (response['status'] == 'need_city') {
        agentReply = response['message'] ?? "Which city?";
        if (mounted) {
          setState(() {
            _lastService = response['service'];
            _awaitingCity = true;
            _awaitingArea = false;
          });
        }
      } else if (response['status'] == 'need_area') {
        // Bot is asking for the area — show clarification message + chips
        agentReply = response['message'] ?? "Pehle area select karein.";
        if (mounted) {
          setState(() {
            _lastService = response['service'];
            _lastCity = response['city'];
            _awaitingArea = true;
          });
        }
      } else if (response['status'] == 'show_providers') {
        // Providers found — show cards below the message bubble
        agentReply = response['message'] ?? "Providers found:";
        if (mounted) {
          setState(() {
            _awaitingArea = false;
            _awaitingCity = false;
            _lastService = null;
            _lastCity = null;
          });
        }
      } else if (response['status'] == 'success' && response['booking_details'] != null) {
        // Booking confirmed
        agentReply = response['booking_details']['message'] ?? "Your booking has been confirmed!";
      } else if (response['status'] == 'failed') {
        // Generic failure
        agentReply = response['message'] ?? response['error'] ?? "An error occurred.";
        isError = true;
      } else if (response['message'] != null) {
        agentReply = response['message'];
      }

      if (mounted) {
        setState(() {
          _messages.add(ChatMessage(
            text: agentReply,
            isUser: false,
            contextData: response,
            isError: isError,
          ));
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add(ChatMessage(
            text: e.toString().replaceAll("Exception: ", ""),
            isUser: false,
            isError: true,
          ));
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            padding: EdgeInsets.all(16),
            itemCount: _messages.length,
            itemBuilder: (context, index) {
              final msg = _messages[index];
              return _buildMessageBubble(msg);
            },
          ),
        ),
        if (_isLoading) _buildThinkingIndicator(),
        _buildMessageInput(),
      ],
    );
  }

  Widget _buildThinkingIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Row(
        children: [
          Text("Agent is thinking", style: TextStyle(color: Colors.grey[600], fontStyle: FontStyle.italic)),
          SizedBox(width: 8),
          AnimatedBuilder(
            animation: _animController,
            builder: (context, child) {
              int dots = (_animController.value * 4).floor();
              return Text("." * dots, style: TextStyle(color: Colors.grey[600], fontStyle: FontStyle.italic));
            },
          ),
        ],
      ),
    );
  }

  void _showFakeBookingConfirmationDialog(ProviderModel provider, Map<String, dynamic> contextData) {
    final serviceDetails = contextData['service_details'] ?? {};
    final service = serviceDetails['service'] ?? 'service';
    final now = DateTime.now();
    final randId = "SRV-${now.year}${now.month.toString().padLeft(2,'0')}${now.day.toString().padLeft(2,'0')}-${now.millisecondsSinceEpoch.toString().substring(9)}";

    // Schedule times
    final slotTime = DateTime(now.year, now.month, now.day + 1, 9, 0);
    final reminderTime = slotTime.subtract(Duration(hours: 1));
    final slotFormatted = "Tomorrow, ${slotTime.hour}:${slotTime.minute.toString().padLeft(2,'0')} AM";
    final reminderFormatted = "${reminderTime.day}/${reminderTime.month} at ${reminderTime.hour}:${reminderTime.minute.toString().padLeft(2,'0')}";

    final serviceLabel = service.toString().replaceAll('_', ' ');
    final capitalService = serviceLabel[0].toUpperCase() + serviceLabel.substring(1);

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          contentPadding: EdgeInsets.zero,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          content: SingleChildScrollView(
            child: Container(
              width: double.maxFinite,
              padding: EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      Container(
                        padding: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Color(0xFF48BB78).withOpacity(0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(Icons.check_circle_rounded, color: Color(0xFF38A169), size: 28),
                      ),
                      SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("Booking Confirmed!", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF276749))),
                          Text("ID: $randId", style: TextStyle(fontSize: 11, color: Colors.grey[600], fontFamily: 'monospace')),
                        ],
                      ),
                    ],
                  ),
                  SizedBox(height: 16),
                  Divider(color: Colors.grey[200]),
                  SizedBox(height: 8),
                  // Booking details
                  _dialogRow(Icons.build_circle_outlined, "Service", capitalService, Colors.blue[700]!),
                  SizedBox(height: 8),
                  _dialogRow(Icons.person_pin_rounded, "Provider", provider.name, Colors.purple[700]!),
                  SizedBox(height: 8),
                  _dialogRow(Icons.schedule_rounded, "Scheduled", slotFormatted, Colors.orange[700]!),
                  SizedBox(height: 16),
                  Divider(color: Colors.grey[200]),
                  SizedBox(height: 8),
                  // Simulated SMS
                  Text("📱 Simulated Notifications Sent", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF2D3748))),
                  SizedBox(height: 8),
                  _smsLog("To You (0300-XXXXXXX)", "Booking $randId confirmed. ${provider.name} will arrive $slotFormatted."),
                  SizedBox(height: 6),
                  _smsLog("To Provider (${provider.phone})", "New job $randId. Location: ${serviceDetails['location'] ?? 'Shared'}. Time: $slotFormatted."),
                  SizedBox(height: 16),
                  Divider(color: Colors.grey[200]),
                  SizedBox(height: 8),
                  // Follow-up reminders
                  Text("⏰ Follow-Up Reminders Scheduled", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF2D3748))),
                  SizedBox(height: 8),
                  _reminderRow("1 hour before appointment", reminderFormatted, true),
                  SizedBox(height: 6),
                  _reminderRow("Completion confirmation", "After service done", false),
                  SizedBox(height: 20),
                  // Status stepper
                  Row(
                    children: [
                      _statusStep("Booked", true, Colors.green),
                      Expanded(child: Container(height: 2, color: Colors.orange[300])),
                      _statusStep("Notified", true, Colors.orange),
                      Expanded(child: Container(height: 2, color: Colors.grey[300])),
                      _statusStep("En Route", false, Colors.grey[400]!),
                      Expanded(child: Container(height: 2, color: Colors.grey[300])),
                      _statusStep("Done", false, Colors.grey[400]!),
                    ],
                  ),
                  SizedBox(height: 20),
                  // Action buttons
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        child: Text("Close", style: TextStyle(color: Colors.grey)),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                      SizedBox(width: 8),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF2C5282),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: Text("View in Chat"),
                        onPressed: () {
                          Navigator.pop(ctx);
                          setState(() {
                            _messages.add(ChatMessage(
                              text: "✅ Booking Confirmed!\n🆔 ID: $randId\n👤 Provider: ${provider.name}\n⏰ Scheduled: $slotFormatted\n📱 SMS sent to you & provider\n🔔 Reminder set for $reminderFormatted",
                              isUser: false,
                            ));
                          });
                          _scrollToBottom();
                        },
                      )
                    ],
                  )
                ],
              ),
            ),
          ),
        );
      }
    );
  }

  Widget _dialogRow(IconData icon, String label, String value, Color color) {
    return Row(
      children: [
        Icon(icon, size: 18, color: color),
        SizedBox(width: 8),
        Text("$label: ", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
        Expanded(child: Text(value, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13), overflow: TextOverflow.ellipsis)),
      ],
    );
  }

  Widget _smsLog(String recipient, String message) {
    return Container(
      padding: EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Color(0xFFEBF8FF),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Color(0xFF90CDF4), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.sms_rounded, size: 13, color: Colors.blue[700]),
              SizedBox(width: 4),
              Text(recipient, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.blue[800])),
            ],
          ),
          SizedBox(height: 3),
          Text(message, style: TextStyle(fontSize: 11, color: Colors.blue[900])),
        ],
      ),
    );
  }

  Widget _reminderRow(String label, String time, bool sent) {
    return Row(
      children: [
        Icon(sent ? Icons.alarm_on_rounded : Icons.alarm_rounded, size: 16, color: sent ? Colors.orange : Colors.grey),
        SizedBox(width: 8),
        Expanded(child: Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[700]))),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: sent ? Colors.orange[50] : Colors.grey[100],
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: sent ? Colors.orange[200]! : Colors.grey[300]!, width: 1),
          ),
          child: Text(time, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: sent ? Colors.orange[800] : Colors.grey[600])),
        ),
      ],
    );
  }

  Widget _statusStep(String label, bool active, Color color) {
    return Column(
      children: [
        Container(
          width: 14, height: 14,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 9, color: color, fontWeight: active ? FontWeight.bold : FontWeight.normal)),
      ],
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    List<dynamic> providers = [];
    if (message.contextData != null && message.contextData!['providers'] != null) {
      providers = message.contextData!['providers'];
    }
    
    Map<String, dynamic>? bookingDetails;
    if (message.contextData != null && message.contextData!['booking_details'] != null) {
      bookingDetails = message.contextData!['booking_details'];
    }

    Color bgColor = message.isUser 
        ? const Color(0xFFE3F2FD) // Light blue for user
        : (message.isError ? const Color(0xFFFFEBEE) : Colors.white); // Soft red for error, white for bot
        
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      child: Column(
        crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(20).copyWith(
                bottomRight: message.isUser ? Radius.circular(4) : Radius.circular(20),
                bottomLeft: !message.isUser ? Radius.circular(4) : Radius.circular(20),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 5,
                  offset: Offset(0, 2),
                )
              ],
              border: Border.all(
                color: message.isUser ? Colors.blue.withOpacity(0.1) : Colors.grey.withOpacity(0.1),
                width: 1,
              ),
            ),
            child: Text(
              message.text,
              style: TextStyle(
                color: const Color(0xFF2D3748),
                fontSize: 15,
                height: 1.4,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          
          if (providers.isNotEmpty) ...[
            SizedBox(height: 8),
            _buildInlineProviderCards(providers, message.contextData!),
          ],
          
          if (message.contextData != null &&
              message.contextData!['suggested_cities'] != null &&
              (message.contextData!['suggested_cities'] as List).isNotEmpty) ...[
            SizedBox(height: 8),
            _buildQuickSelectCities(message.contextData!['suggested_cities']),
          ],
          
          if (message.contextData != null &&
              message.contextData!['suggested_areas'] != null &&
              (message.contextData!['suggested_areas'] as List).isNotEmpty) ...[
            SizedBox(height: 8),
            _buildQuickSelectAreas(message.contextData!['suggested_areas']),
          ],
          
          if (bookingDetails != null) ...[
            SizedBox(height: 8),
            _buildInlineBookingCard(bookingDetails),
          ],
        ],
      ),
    );
  }

  Widget _buildQuickSelectCities(List<dynamic> cities) {
    if (cities.isEmpty) return SizedBox.shrink();
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: cities.map((city) {
        return InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () {
            _sendMessage(overrideText: city.toString());
          },
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 18, vertical: 10),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF4C51BF), Color(0xFF553C9A)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(color: Color(0xFF4C51BF).withOpacity(0.35), blurRadius: 8, offset: Offset(0, 3))
              ],
            ),
            child: Text(
              city.toString(),
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildQuickSelectAreas(List<dynamic> areas) {
    if (areas.isEmpty) return SizedBox.shrink();
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: areas.map((area) {
        return InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () {
            _sendMessage(overrideText: area.toString());
          },
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF38B2AC), Color(0xFF319795)], // Teal gradient
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Color(0xFF319795).withOpacity(0.3),
                  blurRadius: 6,
                  offset: Offset(0, 3),
                ),
              ],
            ),
            child: Text(
              area.toString(),
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildInlineProviderCards(List<dynamic> providers, Map<String, dynamic> contextData) {
    final serviceDetails = contextData['service_details'] ?? {};
    final locationName = serviceDetails['location'] ?? 'Unknown Area';
    
    return Container(
      margin: EdgeInsets.only(top: 12, bottom: 8, left: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.location_on, size: 16, color: Colors.blue[700]),
                SizedBox(width: 6),
                Flexible(
                  child: Text(
                    locationName, 
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue[800], fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                )
              ],
            ),
          ),
          SizedBox(height: 12),
          ...providers.take(3).map((p) {
            final provider = ProviderModel.fromJson(p);
            return Container(
              margin: EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: Offset(0, 4)),
                  BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 2, offset: Offset(0, 1)),
                ],
                border: Border.all(color: Colors.grey.withOpacity(0.1), width: 1),
              ),
              child: Material(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(16),
                child: InkWell(
                  onTap: () => _showFakeBookingConfirmationDialog(provider, contextData),
                  borderRadius: BorderRadius.circular(16),
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              height: 50,
                              width: 50,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [Color(0xFF4299E1), Color(0xFF3182CE)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(color: Color(0xFF4299E1).withOpacity(0.4), blurRadius: 8, offset: Offset(0, 2)),
                                ],
                              ),
                              child: Icon(Icons.person, color: Colors.white, size: 28),
                            ),
                            SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    provider.name, 
                                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF2D3748))
                                  ),
                                  SizedBox(height: 4),
                                  Row(
                                    children: [
                                      Icon(Icons.star_rounded, color: Colors.amber, size: 18),
                                      SizedBox(width: 4),
                                      Text("${provider.rating}", style: TextStyle(fontWeight: FontWeight.w600, color: Colors.grey[700])),
                                      SizedBox(width: 12),
                                      Icon(Icons.directions_car_rounded, color: Colors.grey[500], size: 18),
                                      SizedBox(width: 4),
                                      Text("${provider.distanceKm} km", style: TextStyle(color: Colors.grey[600])),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 10),
                        // Reasoning chip — shows WHY this provider was recommended
                        Container(
                          width: double.infinity,
                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Color(0xFFF0FFF4),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Color(0xFF9AE6B4), width: 1),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.lightbulb_outline_rounded, size: 14, color: Color(0xFF38A169)),
                              SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  provider.reasoning.isNotEmpty ? provider.reasoning : "Best match for your location.",
                                  style: TextStyle(fontSize: 12, color: Color(0xFF276749), height: 1.4),
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          width: double.infinity,
                          height: 44,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [Color(0xFF48BB78), Color(0xFF38A169)], // Green gradient
                              begin: Alignment.centerLeft,
                              end: Alignment.centerRight,
                            ),
                            borderRadius: BorderRadius.circular(10),
                            boxShadow: [
                              BoxShadow(color: Color(0xFF48BB78).withOpacity(0.4), blurRadius: 8, offset: Offset(0, 3)),
                            ],
                          ),
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            child: Text("Book Now", style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                            onPressed: () {
                              _showFakeBookingConfirmationDialog(provider, contextData);
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildInlineBookingCard(Map<String, dynamic> bookingDetails) {
    return Container(
      margin: EdgeInsets.only(top: 8, bottom: 8, left: 16),
      width: 250,
      child: Card(
        color: const Color(0xFFE8F5E9), // Light green
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.green, width: 1)),
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green),
                  SizedBox(width: 8),
                  Text("Confirmed", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green[800])),
                ],
              ),
              Divider(),
              Text("ID: ${bookingDetails['booking_id']}", style: TextStyle(fontWeight: FontWeight.bold)),
              SizedBox(height: 4),
              Text("Status: ${bookingDetails['status']}"),
              SizedBox(height: 8),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF075E54),
                  foregroundColor: Colors.white,
                  minimumSize: Size(double.infinity, 36),
                ),
                child: Text("View Details"),
                onPressed: () {
                  Navigator.push(context, MaterialPageRoute(
                    builder: (_) => BookingScreen(booking: Booking.fromJson(bookingDetails))
                  ));
                },
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: Offset(0, -2)),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Color(0xFFF4F7F6),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: Colors.grey.withOpacity(0.2), width: 1),
              ),
              child: TextField(
                controller: _controller,
                keyboardType: TextInputType.text,
                style: TextStyle(fontSize: 15),
                decoration: InputDecoration(
                  hintText: "Mujhe plumber chahiye...",
                  hintStyle: TextStyle(color: Colors.grey[500]),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
          ),
          SizedBox(width: 12),
          Container(
            height: 52,
            width: 52,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF2B6CB0), Color(0xFF2C5282)], // Blue gradient
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: Color(0xFF2B6CB0).withOpacity(0.4), blurRadius: 8, offset: Offset(0, 3)),
              ],
            ),
            child: IconButton(
              icon: Icon(Icons.send_rounded, color: Colors.white, size: 24),
              onPressed: _sendMessage,
            ),
          )
        ],
      ),
    );
  }
}


