import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/models.dart';

class BookingScreen extends StatefulWidget {
  final Booking booking;

  BookingScreen({required this.booking});

  @override
  _BookingScreenState createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _scaleAnimation = CurvedAnimation(parent: _animController, curve: Curves.elasticOut);
    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F5),
      appBar: AppBar(
        title: Text('Booking Confirmation', style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFF075E54),
        automaticallyImplyLeading: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            SizedBox(height: 20),
            ScaleTransition(
              scale: _scaleAnimation,
              child: Container(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.green[100],
                ),
                padding: EdgeInsets.all(20),
                child: Icon(Icons.check_circle, color: Colors.green[700], size: 80),
              ),
            ),
            SizedBox(height: 24),
            Text(
              'Booking Confirmed!',
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: const Color(0xFF075E54)),
            ),
            SizedBox(height: 30),
            
            // Booking Details Card
            Card(
              elevation: 3,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Booking Details", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey[800])),
                    Divider(height: 24),
                    _buildDetailRow('Provider', widget.booking.providerName ?? 'Assigned Provider'),
                    SizedBox(height: 12),
                    _buildDetailRow('Scheduled Time', widget.booking.scheduledTime ?? 'ASAP'),
                    SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Booking ID', style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                        Row(
                          children: [
                            Text(widget.booking.bookingId, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            IconButton(
                              icon: Icon(Icons.copy, size: 16, color: const Color(0xFF075E54)),
                              padding: EdgeInsets.zero,
                              constraints: BoxConstraints(),
                              onPressed: () {
                                Clipboard.setData(ClipboardData(text: widget.booking.bookingId));
                                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('ID copied to clipboard!')));
                              },
                            )
                          ],
                        )
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(height: 24),
            
            // SMS Simulation
            if (widget.booking.simulatedLogs.isNotEmpty) ...[
              Align(
                alignment: Alignment.centerLeft,
                child: Text('SMS Simulation Logs:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.grey[800])),
              ),
              SizedBox(height: 12),
              ...widget.booking.simulatedLogs.map((log) {
                bool isUserSms = log.toLowerCase().contains("user");
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Align(
                    alignment: isUserSms ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: isUserSms ? const Color(0xFFDCF8C6) : Colors.blue[100],
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 2, offset: Offset(0, 1))],
                      ),
                      child: Text(log, style: TextStyle(fontSize: 14, color: Colors.black87)),
                    ),
                  ),
                );
              }).toList(),
            ],
            
            SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: Icon(Icons.chat),
                label: Text('New Request', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF075E54),
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () {
                  Navigator.popUntil(context, ModalRoute.withName('/'));
                },
              ),
            ),
            SizedBox(height: 12),
            TextButton(
              onPressed: () {
                // Navigate to logs tab. In this setup, we just pop to root since BottomNav is there
                Navigator.popUntil(context, ModalRoute.withName('/'));
              },
              child: Text('View Agent Logs', style: TextStyle(color: const Color(0xFF128C7E), fontWeight: FontWeight.bold)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 14)),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.black87)),
      ],
    );
  }
}
