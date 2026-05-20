import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'booking_screen.dart';

class ProviderListScreen extends StatefulWidget {
  final Map<String, dynamic> contextData;

  ProviderListScreen({required this.contextData});

  @override
  _ProviderListScreenState createState() => _ProviderListScreenState();
}

class _ProviderListScreenState extends State<ProviderListScreen> {
  final HttpService _httpService = HttpService();
  List<ProviderModel> _providers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProviders();
  }

  void _loadProviders() async {
    try {
      if (widget.contextData['top_providers'] != null) {
        _providers = (widget.contextData['top_providers'] as List)
            .map((p) => ProviderModel.fromJson(p))
            .toList();
      } else {
        final serviceType = widget.contextData['intent_data']?['service_type'] ?? 'all';
        _providers = await _httpService.getProviders(serviceType);
        // Simple client-side sorting by score for fallback
        _providers.sort((a, b) => b.score.compareTo(a.score));
      }
    } catch (e) {
      print("Error loading providers: $e");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _bookProvider(ProviderModel provider) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Center(child: CircularProgressIndicator(color: const Color(0xFF075E54))),
    );
    try {
      Booking finalBooking;
      try {
        finalBooking = await _httpService.bookProvider(provider.id, widget.contextData);
      } catch(e) {
         // Fallback mock booking for UI demonstration
         finalBooking = Booking(
          bookingId: "SRV-20260520-X${provider.id.substring(provider.id.length - 3)}",
          status: "confirmed",
          message: "Aapki booking ${provider.name} ke sath confirm ho gayi hai.",
          scheduledTime: widget.contextData['intent_data']?['time'] ?? "As soon as possible",
          providerName: provider.name,
          simulatedLogs: ["SMS sent to User: Provider is arriving", "SMS sent to Provider: New job at ${widget.contextData['intent_data']?['location_name'] ?? 'Location'}"],
        );
      }
      
      Navigator.pop(context); // Close dialog

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => BookingScreen(booking: finalBooking),
        ),
      );
    } catch (e) {
      Navigator.pop(context); // Close dialog
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to book: $e'), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F5),
      appBar: AppBar(
        title: Text('Top Providers Near You', style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFF075E54),
        iconTheme: IconThemeData(color: Colors.white),
      ),
      body: _isLoading
          ? _buildSkeletonLoader()
          : _providers.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  padding: EdgeInsets.all(16),
                  itemCount: _providers.take(3).length, // Requirement: Top 3
                  itemBuilder: (context, index) {
                    final provider = _providers[index];
                    return _buildProviderCard(provider, index + 1);
                  },
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text("😞", style: TextStyle(fontSize: 64)),
          SizedBox(height: 16),
          Text(
            "No providers available",
            style: TextStyle(fontSize: 20, color: Colors.grey[700], fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text("Please try a different time or area.", style: TextStyle(color: Colors.grey[600])),
        ],
      ),
    );
  }

  Widget _buildSkeletonLoader() {
    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: 3,
      itemBuilder: (context, index) {
        return Card(
          margin: EdgeInsets.only(bottom: 16),
          child: Container(
            height: 180,
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(height: 24, width: 150, color: Colors.grey[300]),
                SizedBox(height: 16),
                Container(height: 16, width: double.infinity, color: Colors.grey[200]),
                SizedBox(height: 8),
                Container(height: 16, width: double.infinity, color: Colors.grey[200]),
                Spacer(),
                Container(height: 40, width: double.infinity, color: Colors.grey[300]),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildProviderCard(ProviderModel provider, int rank) {
    Color rankColor = rank == 1 ? Colors.amber : (rank == 2 ? Colors.blueGrey : Colors.brown[300]!);
    
    // Calculate breakdowns safely
    double maxDistanceScore = 40.0;
    double actualDistanceScore = (40 - (provider.distanceKm * 2)).clamp(0, 40).toDouble();
    double ratingScore = ((provider.rating / 5.0) * 40).toDouble();
    double availScore = 20.0;

    return Card(
      elevation: 4,
      margin: EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: rankColor,
                  radius: 14,
                  child: Text('#$rank', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    provider.name,
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.directions_car, size: 18, color: Colors.grey[600]),
                SizedBox(width: 4),
                Text('${provider.distanceKm} km', style: TextStyle(color: Colors.grey[800], fontWeight: FontWeight.w500)),
                SizedBox(width: 16),
                Icon(Icons.star, size: 18, color: Colors.amber),
                SizedBox(width: 4),
                Text('${provider.rating}', style: TextStyle(color: Colors.grey[800], fontWeight: FontWeight.w500)),
              ],
            ),
            SizedBox(height: 16),
            
            // Visual Score Bar
            Text('Overall Match Score: ${provider.score.toStringAsFixed(1)}/100', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            SizedBox(height: 4),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: provider.score / 100.0,
                minHeight: 8,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(const Color(0xFF075E54)),
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Distance: ${actualDistanceScore.toStringAsFixed(0)}/40, Rating: ${ratingScore.toStringAsFixed(0)}/40, Available: ${availScore.toStringAsFixed(0)}/20',
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            
            SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => _bookProvider(provider),
                child: Text('Select & Book', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF075E54),
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}
