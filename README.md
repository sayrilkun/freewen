# FreeWen ✈️ - AI Travel Planning Companion

FreeWen is an intelligent travel planning application powered by Google Gemini AI that helps you create comprehensive, personalized travel itineraries with real-time information from Google Search.

## ✨ Features

### 🗺️ Intelligent Trip Planning
- **AI-Powered Itineraries**: Generate detailed day-by-day travel plans with hour-by-hour schedules
- **Real-Time Data**: Powered by Google Gemini with Google Search grounding for up-to-date information
- **Multi-Currency Support**: Plan trips in your preferred currency (USD, EUR, GBP, JPY, AUD, CAD, CNY, INR)
- **Multi-Traveler Support**: Plan for solo trips or group travel with automatic cost calculations

### 📋 Comprehensive Travel Information
- **Flight Options**: Compare multiple flight options with pricing and booking links
- **Hotel Recommendations**: Get 4-6 hotel suggestions matching your accommodation preferences
- **Detailed Itineraries**: Hour-by-hour schedules including:
  - Specific times for each activity
  - Transportation details between locations
  - Meal recommendations (breakfast, lunch, dinner, snacks)
  - Activity costs and durations
  - Direct Google Maps links for every location
- **Budget Breakdown**: Detailed cost analysis by category

### 🎯 Personalization Options
- **Travel Pace**: Choose between Relaxed, Moderate, or Fast-paced trips
- **Travel Style**: Select from Adventure, Cultural, Luxury, Budget-friendly, or Family-friendly
- **Activities**: Customize with Sightseeing, Food & Dining, Shopping, Nature & Outdoors, Museums & Art, or Nightlife
- **Custom Activities**: Add your own specific interests
- **Accommodation Preferences**: Hotel, Hostel, Airbnb, or Resort
- **Dietary Preferences**: No restrictions, Vegetarian, Vegan, or Halal options

### 🗂️ Trip Management
- **Multiple Travel Sessions**: Manage multiple trip plans simultaneously
- **Session Persistence**: All plans are saved in your session
- **Bookings & Tickets Tab**: Upload and organize travel documents
  - Support for PDFs, images (JPG, PNG), and documents (DOCX)
  - Download organized booking files
- **Export Functionality**: Download itineraries and data as Excel files

### 🗺️ Interactive Map Panel
- **Fixed Right Sidebar**: Collapsible map panel that stays visible while scrolling
- **Trip Summary Card**: Quick view of destination, dates, and budget
- **Location Pins**: Click on any location to view it on Google Maps
- **Expandable Location List**: Browse all itinerary locations with one-click map access

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sayrilkun/freewen.git
   cd freewen
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   To get a Gemini API key:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Create a new API key
   - Copy and paste it into your `.env` file

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the app**
   
   Open your browser and navigate to `http://localhost:8501`

## 📖 How to Use

### Creating Your First Trip

1. **Start a New Travel Plan**
   - Click "➕ New Travel Plan" in the sidebar
   - Enter a name for your trip (e.g., "Tokyo Adventure 2025")

2. **Enter Trip Details**
   - **Origin City**: Where you'll be traveling from
   - **Destination**: Your travel destination
   - **Travel Dates**: Select start and end dates
   - **Number of Travelers**: How many people are traveling
   - **Budget**: Total budget for all travelers
   - **Currency**: Select your preferred currency

3. **Customize Preferences**
   - **Travel Pace**: How fast-paced you want your trip to be
   - **Travel Style**: Your preferred travel experience
   - **Activities**: What you want to do (select multiple)
   - **Custom Activities**: Add specific interests not listed
   - **Accommodation Type**: Where you prefer to stay
   - **Food Preferences**: Any dietary restrictions

4. **Generate Your Plan**
   - Click "✨ Generate Travel Plan"
   - Wait for AI to create your personalized itinerary (may take 30-60 seconds)

5. **Review Your Itinerary**
   - Browse flight options with direct booking links
   - Compare hotel recommendations
   - View day-by-day itinerary with hour-by-hour schedule
   - Check budget breakdown by category
   - Click location pins in the map panel to explore on Google Maps

6. **Export Your Plan**
   - Click "📥 Download Travel Plan (Excel)" to save all data
   - Files include separate sheets for flights, hotels, itinerary, and budget

### Managing Multiple Trips

- Switch between trips using the sidebar dropdown
- Each session maintains its own:
  - Travel preferences
  - Generated itinerary
  - Uploaded booking documents
  - Budget calculations

### Organizing Bookings & Tickets

1. Navigate to the "🎫 Bookings & Tickets" tab
2. Upload your travel documents:
   - Flight confirmations
   - Hotel vouchers
   - Activity tickets
   - Visa documents
3. Download all bookings as organized files

### Using the Interactive Map

- **Toggle Map Panel**: Click the floating "🗺️ MAP" button on the right
- **View Locations**: Click any location button to see it on Google Maps
- **Expand Location List**: Click "Show all locations" to see complete list
- **Navigate**: Map updates in real-time as you click different locations

## 🛠️ Technical Details

### Built With
- **Streamlit**: Web framework for the user interface
- **Google Gemini 2.5 Flash**: AI model for travel plan generation
- **Google Search Grounding**: Real-time travel information
- **Pandas**: Data manipulation and Excel export
- **Python dotenv**: Environment variable management

### Project Structure
```
freewen/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── README.md          # This file
└── assets/            # Logo and images (if any)
```

### Key Functions
- `generate_travel_plan()`: Calls Gemini API with Google Search grounding
- `parse_and_display_travel_plan()`: Parses AI response into structured tables
- `create_travel_session()`: Manages multiple trip sessions
- Interactive map panel with location extraction and Google Maps integration

## 📊 Data Export

Export formats include:
- **Excel (.xlsx)**: Complete travel plan with multiple sheets
  - Flights sheet
  - Hotels sheet
  - Itinerary sheet (organized by day)
  - Budget sheet
- **Individual Downloads**: Booking documents as uploaded

## 🎨 Customization

### Adding Custom Activities
1. Go to Travel Preferences section
2. Enter custom activities separated by commas
3. Example: "Photography, Wine Tasting, Yoga Classes"

### Budget Management
- All costs are automatically calculated for the number of travelers
- Budget breakdown shows spending by category:
  - Flights
  - Accommodation
  - Food & Dining
  - Activities & Entertainment
  - Transportation

## 🔒 Privacy & Data

- All data is stored in session state (temporary)
- No personal information is sent to external servers except to Gemini API
- Uploaded files are stored in memory only
- Session data is cleared when you close the browser

## 🐛 Troubleshooting

### Common Issues

**"API Key not found" error**
- Ensure you created a `.env` file in the project root
- Verify your API key is correct
- Restart the Streamlit app after creating `.env`

**"No response from AI" or slow generation**
- Google Gemini may be rate-limited or experiencing high traffic
- Wait a moment and try again
- Check your internet connection

**Map not loading**
- Ensure JavaScript is enabled in your browser
- Check browser console for errors
- Try refreshing the page

**Export not working**
- Ensure you've generated a travel plan first
- Check browser's download settings
- Try a different browser

## 🤝 Contributing

Contributions are welcome! Please feel free to:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google Gemini API for AI-powered travel planning
- Streamlit for the amazing web framework
- Google Maps for location services

## 📧 Contact

For questions, issues, or suggestions:
- Create an issue on GitHub
- Contact: [Your contact information]

## 🗺️ Roadmap

Future enhancements planned:
- [ ] Multi-language support
- [ ] Weather integration
- [ ] Real-time flight price tracking
- [ ] Collaborative trip planning
- [ ] Mobile app version
- [ ] Integration with booking platforms
- [ ] Travel expense tracker
- [ ] Community itinerary sharing

---

**Happy Travels with FreeWen!** ✈️🌍

Made with ❤️ using AI and modern web technologies.
