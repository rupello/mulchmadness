### Scripts for Troop 158 Mulch Routes

#### Instructions
* Place `Sales tracker_2017.xlsx` and `MASTER Mulch Database_17.xls` in the `./data` folder
* Run `python geocode_orders.py` to normalize and geocode data - this outputs `./data/tracker_norm.xls`
* Manually assign routes in `./data/tracker_norm.xls` by updating the `route_number` field
    * All `pipestem` orders should go in a pickup truck
    * Route for the flat-bed is very restricted - see maps from last year
    * I make route maps in 'My Google Maps' for box truck and flat-bed 
    * A preloaded box truck can hold five pallets (225 bags).
    * The semi can hold seven pallets (315 bags).
    * Small pickups can carry 20 bags.
    * Larger pickups can safely carry 35 bags.
    * If you rent a 12-foot flatbed, it can carry three pallets (135 bags).
    * **Adjust appropriately if the mulch is wet and heavy:**
* Run `python route_report.py` to generate pdf reports for deliveries
* Print two copies of all manifests - one for driver, one for co-ordinator